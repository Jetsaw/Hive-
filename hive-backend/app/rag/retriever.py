from typing import List, Dict, Tuple
import re
import faiss
from app.rag.embeddings import embed_query
from app.core.config import settings

COURSE_CODE_RE = re.compile(r"\b[A-Z]{3}\d{4}\b")


def search(index: faiss.Index, metas: List[Dict], query: str, top_k: int | None = None) -> List[Dict]:
    if top_k is None:
        top_k = settings.TOP_K

    if index is None or metas is None or index.ntotal == 0:
        return []

    q = embed_query(query).reshape(1, -1)
    scores, ids = index.search(q, top_k)

    results: list[dict] = []
    for score, idx in zip(scores[0].tolist(), ids[0].tolist()):
        if idx == -1:
            continue
        m = metas[idx]
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

    # 🔹 HYBRID FILTER: exact course code match
    codes = COURSE_CODE_RE.findall(query.upper())
    if codes:
        filtered = []
        for r in results:
            txt = (r.get("text") or "").upper()
            if any(code in txt for code in codes):
                filtered.append(r)

        # Only override if we found matches
        if filtered:
            results = filtered

    return results


def build_context(results: List[Dict]) -> Tuple[str, List[Dict]]:
    good = [r for r in results if r.get("score", 0.0) >= settings.MIN_SCORE]
    if not good:
        return "", []

    ctx_parts: list[str] = []
    total = 0

    for r in good:
        snippet = (r.get("text") or "").strip()
        if not snippet:
            continue

        if total + len(snippet) > settings.MAX_CONTEXT_CHARS:
            break

        total += len(snippet)
        ctx_parts.append(snippet)

    # 🔹 UI requirement: no sources returned
    return "\n\n".join(ctx_parts), []
