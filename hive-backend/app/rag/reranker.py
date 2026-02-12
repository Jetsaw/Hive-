from typing import List, Dict, Tuple
from sentence_transformers import CrossEncoder
import numpy as np


class Reranker:
    """
    Cross-encoder reranker for improving retrieval precision.
    Uses a cross-encoder model to score query-document pairs.
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2"):
        """
        Initialize the reranker with a cross-encoder model.
        
        Args:
            model_name: HuggingFace cross-encoder model name
        """
        self._model = CrossEncoder(model_name)
    
    def rerank(
        self,
        query: str,
        results: List[Dict],
        top_k: int | None = None
    ) -> List[Dict]:
        """
        Rerank search results using cross-encoder scoring.
        
        Args:
            query: The search query
            results: List of search results with 'text' field
            top_k: Number of top results to return (default: all)
        
        Returns:
            Reranked list of results with updated scores
        """
        if not results:
            return []
        
        # Prepare query-document pairs
        pairs = [(query, r.get("text", "")) for r in results]
        
        # Get cross-encoder scores
        scores = self._model.predict(pairs)
        
        # Update results with reranked scores
        reranked = []
        for idx, result in enumerate(results):
            result_copy = dict(result)
            result_copy["rerank_score"] = float(scores[idx])
            result_copy["original_score"] = result.get("score", 0.0)
            # Replace score with rerank score
            result_copy["score"] = float(scores[idx])
            reranked.append(result_copy)
        
        # Sort by new scores
        reranked.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top_k if specified
        if top_k:
            return reranked[:top_k]
        return reranked


# Global reranker instance (lazy loaded)
_reranker: Reranker | None = None


def get_reranker() -> Reranker:
    """Get or create the global reranker instance."""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker


def rerank_results(
    query: str,
    results: List[Dict],
    top_k: int | None = None
) -> List[Dict]:
    """
    Convenience function to rerank results.
    
    Args:
        query: The search query
        results: List of search results
        top_k: Number of top results to return
    
    Returns:
        Reranked results
    """
    reranker = get_reranker()
    return reranker.rerank(query, results, top_k)
