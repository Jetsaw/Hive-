from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi
import numpy as np


class HybridSearcher:
    """
    Implements hybrid search combining dense (vector) and sparse (BM25) retrieval.
    Uses Reciprocal Rank Fusion (RRF) to combine scores.
    """
    
    def __init__(self, alpha: float = 0.5):
        """
        Initialize hybrid searcher.
        
        Args:
            alpha: Weight for vector search (1-alpha for BM25). 
                   0.5 = equal weight, 1.0 = vector only, 0.0 = BM25 only
        """
        self.alpha = alpha
        self.bm25_index: BM25Okapi | None = None
        self.tokenized_docs: List[List[str]] = []
    
    def build_bm25_index(self, documents: List[str]):
        """
        Build BM25 index from documents.
        
        Args:
            documents: List of text documents
        """
        # Simple tokenization (split on whitespace and lowercase)
        self.tokenized_docs = [doc.lower().split() for doc in documents]
        self.bm25_index = BM25Okapi(self.tokenized_docs)
    
    def bm25_search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Perform BM25 search.
        
        Args:
            query: Search query
            top_k: Number of results
        
        Returns:
            List of (index, score) tuples
        """
        if self.bm25_index is None:
            return []
        
        tokenized_query = query.lower().split()
        scores = self.bm25_index.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(int(idx), float(scores[idx])) for idx in top_indices]
    
    @staticmethod
    def reciprocal_rank_fusion(
        vector_results: List[Tuple[int, float]],
        bm25_results: List[Tuple[int, float]],
        k: int = 60
    ) -> List[Tuple[int, float]]:
        """
        Combine rankings using Reciprocal Rank Fusion.
        
        Args:
            vector_results: List of (index, score) from vector search
            bm25_results: List of (index, score) from BM25
            k: RRF constant (typically 60)
        
        Returns:
            Fused list of (index, score) tuples
        """
        rrf_scores: Dict[int, float] = {}
        
        # Add vector search scores
        for rank, (idx, _) in enumerate(vector_results, start=1):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (k + rank)
        
        # Add BM25 scores
        for rank, (idx, _) in enumerate(bm25_results, start=1):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (k + rank)
        
        # Sort by fused score
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results
    
    def hybrid_search(
        self,
        query: str,
        vector_results: List[Dict],
        top_k: int = 10
    ) -> List[Dict]:
        """
        Perform hybrid search combining vector and BM25.
        
        Args:
            query: Search query
            vector_results: Results from vector search with 'text' field
            top_k: Number of results to return
        
        Returns:
            Hybrid ranked results
        """
        if self.bm25_index is None or not vector_results:
            return vector_results[:top_k]
        
        # Get BM25 results
        bm25_results = self.bm25_search(query, top_k=len(vector_results))
        
        # Create index to result mapping
        vector_tuples = [(i, r.get("score", 0.0)) for i, r in enumerate(vector_results)]
        
        # Fuse rankings
        fused = self.reciprocal_rank_fusion(vector_tuples, bm25_results)
        
        # Build final result list
        hybrid_results = []
        for idx, rrf_score in fused[:top_k]:
            if idx < len(vector_results):
                result = dict(vector_results[idx])
                result["hybrid_score"] = float(rrf_score)
                result["original_vector_score"] = result.get("score", 0.0)
                result["score"] = float(rrf_score)  # Use hybrid score as primary
                hybrid_results.append(result)
        
        return hybrid_results


# Global hybrid searcher instance
_hybrid_searcher: HybridSearcher | None = None


def get_hybrid_searcher() -> HybridSearcher:
    """Get or create global hybrid searcher."""
    global _hybrid_searcher
    if _hybrid_searcher is None:
        _hybrid_searcher = HybridSearcher()
    return _hybrid_searcher
