from typing import List, Dict, Tuple, Optional
import re
import faiss
from app.rag.embeddings import embed_query
from app.core.config import settings
from app.rag.reranker import rerank_results

COURSE_CODE_RE = re.compile(r"\b[A-Z]{3}\d{4}\b")


def search(index: faiss.Index, metas: List[Dict], query: str, top_k: int | None = None, metadata_filter: Dict[str, str] | None = None, use_reranking: bool = False) -> List[Dict]:
    if top_k is None:
        top_k = settings.TOP_K

    if index is None or metas is None or index.ntotal == 0:
        return []

    # Apply metadata pre-filtering if specified
    if metadata_filter:
        filtered_indices = []
        filtered_metas = []
        for idx, meta in enumerate(metas):
            # Check if all filter conditions match
            if all(meta.get(key) == value for key, value in metadata_filter.items()):
                filtered_indices.append(idx)
                filtered_metas.append(meta)
        
        # If no matches after filtering, return empty
        if not filtered_indices:
            return []
        
        # Create a temporary index with only filtered vectors
        # This is a simplified approach; for production, consider index partitioning
        # For now, we'll search the full index and filter results
        pass  # We'll filter results after retrieval instead
    
    q = embed_query(query).reshape(1, -1)
    
    # Increase search size if filtering to ensure we get enough results
    search_k = top_k * 3 if metadata_filter else top_k
    scores, ids = index.search(q, min(search_k, index.ntotal))

    results: list[dict] = []
    for score, idx in zip(scores[0].tolist(), ids[0].tolist()):
        if idx == -1:
            continue
        m = metas[idx]
        
        # Apply metadata filter
        if metadata_filter:
            if not all(m.get(key) == value for key, value in metadata_filter.items()):
                continue
        
        results.append(
            {
                "score": float(score),
                "source_file": m.get("source_file"),
                "page": m.get("page"),
                "type": m.get("type"),
                "programme": m.get("programme"),
                "text": m.get("text", ""),
            }
        )

    # 🔹 HYBRID BOOST: exact course code match boosts score
    codes = COURSE_CODE_RE.findall(query.upper())
    if codes:
        for r in results:
            txt = (r.get("text") or "").upper()
            if any(code in txt for code in codes):
                r["score"] += 0.3 # Boost score for exact code match

    # Re-sort after boosting
    results.sort(key=lambda x: x["score"], reverse=True)

    # Apply reranking if enabled
    if use_reranking and results:
        results = rerank_results(query, results, top_k)
        return results

    return results[:top_k]


def build_context(results: List[Dict], return_sources: bool = False) -> Tuple[str, List[Dict]]:
    """
    Build context from search results with intelligent truncation.
    
    Args:
        results: List of search results with scores and text
        return_sources: Whether to return source attribution
    
    Returns:
        Tuple of (context_string, sources_list)
    """
    good = [r for r in results if r.get("score", 0.0) >= settings.MIN_SCORE]
    if not good:
        return "", []

    ctx_parts: list[str] = []
    sources: list[dict] = []
    total = 0

    # Sort by score to prioritize highest-scoring chunks
    good.sort(key=lambda x: x.get("score", 0.0), reverse=True)

    for idx, r in enumerate(good):
        snippet = (r.get("text") or "").strip()
        if not snippet:
            continue

        # Check if adding this snippet would exceed limit
        if total + len(snippet) > settings.MAX_CONTEXT_CHARS:
            # Try to add partial snippet if it's the first one
            if idx == 0:
                remaining = settings.MAX_CONTEXT_CHARS - total
                if remaining > 100:  # Only add if meaningful chunk remains
                    snippet = snippet[:remaining] + "..."
                    ctx_parts.append(snippet)
                    total += len(snippet)
            break

        total += len(snippet)
        ctx_parts.append(snippet)
        
        # Track sources if requested
        if return_sources:
            sources.append({
                "source_file": r.get("source_file"),
                "page": r.get("page"),
                "type": r.get("type"),
                "score": r.get("score"),
            })

    context = "\n\n".join(ctx_parts)
    
    # Return sources or empty list based on parameter
    return context, sources if return_sources else []


def search_structure_layer(
    index: faiss.Index, 
    metas: List[Dict], 
    query: str, 
    top_k: int | None = None,
    programme: Optional[str] = None
) -> List[Dict]:
    """
    Search programme structure layer.
    
    Args:
        index: FAISS index for structure layer
        metas: Metadata for structure layer
        query: Search query
        top_k: Number of results
        programme: Optional programme filter
    
    Returns:
        List of search results
    """
    if top_k is None:
        top_k = settings.TOP_K
    
    if index is None or metas is None or index.ntotal == 0:
        return []
    
    q = embed_query(query).reshape(1, -1)
    scores, ids = index.search(q, min(top_k * 2, index.ntotal))  # Get more for filtering
    
    results: list[dict] = []
    for score, idx in zip(scores[0].tolist(), ids[0].tolist()):
        if idx == -1:
            continue
        m = metas[idx]
        
        # Filter by programme if specified
        if programme:
            meta_programme = m.get('programme', '')
            if meta_programme != 'ALL' and meta_programme != programme:
                continue
        
        results.append({
            "score": float(score),
            "id": m.get("id"),
            "type": m.get("type"),
            "programme": m.get("programme"),
            "layer": "structure",
            "text": m.get("text", ""),
            "metadata": {k: v for k, v in m.items() if k not in ['text', 'layer']}
        })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def search_details_layer(
    index: faiss.Index, 
    metas: List[Dict], 
    query: str, 
    course_codes: Optional[List[str]] = None,
    top_k: int | None = None
) -> List[Dict]:
    """
    Search subject details layer with course code filtering.
    
    Args:
        index: FAISS index for details layer
        metas: Metadata for details layer
        query: Search query
        course_codes: Optional list of course codes to filter by
        top_k: Number of results
    
    Returns:
        List of search results
    """
    if top_k is None:
        top_k = settings.TOP_K
    
    if index is None or metas is None or index.ntotal == 0:
        return []
    
    # HALLUCINATION PREVENTION: Require course code for details access
    if not course_codes:
        return []
    
    q = embed_query(query).reshape(1, -1)
    scores, ids = index.search(q, min(top_k * 3, index.ntotal))  # Get more for filtering
    
    results: list[dict] = []
    for score, idx in zip(scores[0].tolist(), ids[0].tolist()):
        if idx == -1:
            continue
        m = metas[idx]
        
        # Filter by course code (STRICT)
        meta_course_code = m.get('course_code', '')
        if meta_course_code not in course_codes:
            continue
        
        results.append({
            "score": float(score),
            "id": m.get("id"),
            "course_code": meta_course_code,
            "course_name": m.get("course_name"),
            "question": m.get("question"),
            "answer": m.get("answer"),
            "layer": "details",
            "text": m.get("text", ""),
            "source": m.get("source")
        })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
