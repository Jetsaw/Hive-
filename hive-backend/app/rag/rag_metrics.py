from typing import List, Dict
import statistics


class RAGMetrics:
    """
    Tracks and calculates RAG retrieval quality metrics.
    """
    
    @staticmethod
    def precision_at_k(results: List[Dict], k: int, relevance_threshold: float = 0.5) -> float:
        """
        Calculate Precision@K - proportion of relevant docs in top-k.
        
        Args:
            results: List of search results with scores
            k: Number of top results to consider
            relevance_threshold: Minimum score to consider relevant
        
        Returns:
            Precision@K score (0-1)
        """
        if not results or k <= 0:
            return 0.0
        
        top_k = results[:k]
        relevant = sum(1 for r in top_k if r.get("score", 0.0) >= relevance_threshold)
        return relevant / len(top_k)
    
    @staticmethod
    def mean_reciprocal_rank(results: List[Dict], relevance_threshold: float = 0.5) -> float:
        """
        Calculate MRR - reciprocal rank of first relevant result.
        
        Args:
            results: List of search results with scores
            relevance_threshold: Minimum score to consider relevant
        
        Returns:
            MRR score (0-1)
        """
        if not results:
            return 0.0
        
        for idx, r in enumerate(results, start=1):
            if r.get("score", 0.0) >= relevance_threshold:
                return 1.0 / idx
        
        return 0.0
    
    @staticmethod
    def average_score(results: List[Dict]) -> float:
        """
        Calculate average relevance score of results.
        
        Args:
            results: List of search results with scores
        
        Returns:
            Average score
        """
        if not results:
            return 0.0
        
        scores = [r.get("score", 0.0) for r in results]
        return statistics.mean(scores)
    
    @staticmethod
    def score_std_dev(results: List[Dict]) -> float:
        """
        Calculate standard deviation of scores - measures score separation.
        
        Args:
            results: List of search results with scores
        
        Returns:
            Standard deviation of scores
        """
        if len(results) < 2:
            return 0.0
        
        scores = [r.get("score", 0.0) for r in results]
        return statistics.stdev(scores)
    
    @staticmethod
    def reranking_impact(results: List[Dict]) -> Dict[str, float]:
        """
        Measure impact of reranking on result order.
        
        Args:
            results: List with both 'original_score' and 'rerank_score'
        
        Returns:
            Dict with reranking metrics
        """
        if not results or "original_score" not in results[0]:
            return {"position_changes": 0, "avg_score_delta": 0.0}
        
        # Count position changes
        original_order = sorted(enumerate(results), key=lambda x: x[1].get("original_score", 0.0), reverse=True)
        rerank_order = sorted(enumerate(results), key=lambda x: x[1].get("rerank_score", 0.0), reverse=True)
        
        position_changes = sum(
            1 for i in range(len(results))
            if original_order[i][0] != rerank_order[i][0]
        )
        
        # Average score delta
        score_deltas = [
            abs(r.get("rerank_score", 0.0) - r.get("original_score", 0.0))
            for r in results
        ]
        avg_delta = statistics.mean(score_deltas) if score_deltas else 0.0
        
        return {
            "position_changes": position_changes,
            "avg_score_delta": avg_delta
        }
    
    @staticmethod
    def compute_all_metrics(results: List[Dict], top_k: int = 3) -> Dict[str, float]:
        """
        Compute all available metrics for a result set.
        
        Args:
            results: List of search results
            top_k: K value for precision@k
        
        Returns:
            Dict of all metrics
        """
        metrics = {
            f"precision@{top_k}": RAGMetrics.precision_at_k(results, top_k),
            "mrr": RAGMetrics.mean_reciprocal_rank(results),
            "avg_score": RAGMetrics.average_score(results),
            "score_std_dev": RAGMetrics.score_std_dev(results),
            "num_results": len(results)
        }
        
        # Add reranking metrics if available
        if results and "original_score" in results[0]:
            rerank_metrics = RAGMetrics.reranking_impact(results)
            metrics.update({
                "rerank_position_changes": rerank_metrics["position_changes"],
                "rerank_avg_score_delta": rerank_metrics["avg_score_delta"]
            })
        
        return metrics
