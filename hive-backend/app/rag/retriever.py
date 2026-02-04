from typing import List, Dict, Tuple, Optional
import re
import faiss
from app.rag.embeddings import embed_query
from app.core.config import settings
from app.rag.reranker import rerank_results

COURSE_CODE_RE = re.compile(r"\b[A-Z]{3}\d{4}\b")

COURSE_CODE_BOOST_SCORE = 0.3
MIN_MEANINGFUL_CHUNK_SIZE = 100
FILTER_SEARCH_MULTIPLIER = 3
STRUCTURE_SEARCH_MULTIPLIER = 2


def search(index: faiss.Index, metas: List[Dict], query: str, top_k: int | None = None, metadata_filter: Dict[str, str] | None = None, use_reranking: bool = False) -> List[Dict]:
    if top_k is None:
        top_k = settings.TOP_K

    if index is None or metas is None or index.ntotal == 0:
        return []

    if metadata_filter:
        filtered_indices = []
        filtered_metas = []
        for idx, meta in enumerate(metas):
            if all(meta.get(key) == value for key, value in metadata_filter.items()):
                filtered_indices.append(idx)
                filtered_metas.append(meta)
        
        if not filtered_indices:
            return []
    
    q = embed_query(query).reshape(1, -1)
    
    search_k = top_k * FILTER_SEARCH_MULTIPLIER if metadata_filter else top_k
    scores, ids = index.search(q, min(search_k, index.ntotal))

    results: list[dict] = []
    for score, idx in zip(scores[0].tolist(), ids[0].tolist()):
        if idx == -1:
            continue
        meta = metas[idx]
        
        if metadata_filter:
            if not all(meta.get(key) == value for key, value in metadata_filter.items()):
                continue
        
        results.append(
            {
                "score": float(score),
                "source_file": meta.get("source_file"),
                "page": meta.get("page"),
                "type": meta.get("type"),
                "programme": meta.get("programme"),
                "text": meta.get("text", ""),
            }
        )

    codes = COURSE_CODE_RE.findall(query.upper())
    if codes:
        for r in results:
            txt = (r.get("text") or "").upper()
            if any(code in txt for code in codes):
                r["score"] += COURSE_CODE_BOOST_SCORE

    results.sort(key=lambda x: x["score"], reverse=True)

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

    good.sort(key=lambda x: x.get("score", 0.0), reverse=True)

    for idx, r in enumerate(good):
        snippet = (r.get("text") or "").strip()
        if not snippet:
            continue

        if total + len(snippet) > settings.MAX_CONTEXT_CHARS:
            if idx == 0:
                remaining = settings.MAX_CONTEXT_CHARS - total
                if remaining > MIN_MEANINGFUL_CHUNK_SIZE:
                    snippet = snippet[:remaining] + "..."
                    ctx_parts.append(snippet)
                    total += len(snippet)
            break

        total += len(snippet)
        ctx_parts.append(snippet)
        
        if return_sources:
            sources.append({
                "source_file": r.get("source_file"),
                "page": r.get("page"),
                "type": r.get("type"),
                "score": r.get("score"),
            })

    context = "\n\n".join(ctx_parts)
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
    scores, ids = index.search(q, min(top_k * STRUCTURE_SEARCH_MULTIPLIER, index.ntotal))
    
    results: list[dict] = []
    for score, idx in zip(scores[0].tolist(), ids[0].tolist()):
        if idx == -1:
            continue
        meta = metas[idx]
        
        if programme:
            meta_programme = meta.get('programme', '')
            if meta_programme != 'ALL' and meta_programme != programme:
                continue
        
        results.append({
            "score": float(score),
            "id": meta.get("id"),
            "type": meta.get("type"),
            "programme": meta.get("programme"),
            "layer": "structure",
            "text": meta.get("text", ""),
            "metadata": {k: v for k, v in meta.items() if k not in ['text', 'layer']}
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
    
    q = embed_query(query).reshape(1, -1)
    scores, ids = index.search(q, min(top_k * FILTER_SEARCH_MULTIPLIER, index.ntotal))
    
    results: list[dict] = []
    for score, idx in zip(scores[0].tolist(), ids[0].tolist()):
        if idx == -1:
            continue
        meta = metas[idx]
        
        # If course_codes provided, filter by them
        if course_codes:
            meta_course_code = meta.get('course_code', '')
            if meta_course_code not in course_codes:
                continue
        
        results.append({
            "score": float(score),
            "id": meta.get("id"),
            "course_code": meta.get("course_code"),
            "course_name": meta.get("course_name"),
            "question": meta.get("question"),
            "answer": meta.get("answer"),
            "layer": "details",
            "text": meta.get("text", ""),
            "source": meta.get("source"),
            "tags": meta.get("tags", [])
        })
    
    # SEMANTIC RE-RANKING: Boost answers matching query intent
    query_lower = query.lower()
    
    for result in results:
        boost = 0.0
        tags = result.get("tags", [])
        question_text = result.get("question", "").lower()
        
        # Boost for "about/overview" questions
        if any(keyword in query_lower for keyword in ["what is", "about", "overview", "describe"]):
            if "overview" in tags or "topics" in tags:
                boost += 0.5  # Strong boost for matching tags
            elif "prerequisite" in tags or "credit" in tags or "assessment" in tags:
                boost -= 0.3  # Strong penalty for non-overview answers
        
        # Boost for prerequisite questions
        elif any(keyword in query_lower for keyword in ["prerequisite", "pre-req", "prereq", "require"]):
            if "prerequisite" in tags:
                boost += 0.5
            elif "overview" in tags:
                boost -= 0.2
        
        # Boost for assessment questions
        elif any(keyword in query_lower for keyword in ["assess", "exam", "test", "graded"]):
            if "assessment" in tags:
                boost += 0.5
        
        # Boost for credit hours questions
        elif any(keyword in query_lower for keyword in ["credit", "hours", "how many"]):
            if "credit_hours" in tags:
                boost += 0.5
        
        # Boost for topic questions
        elif any(keyword in query_lower for keyword in ["topics", "cover", "learn", "content"]):
            if "topics" in tags or "overview" in tags:
                boost += 0.5
        
        # Apply boost to score (higher score = better match)
        result["score"] = result["score"] + boost
        result["boost"] = boost  # For debugging
    
    # Re-sort by adjusted score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
