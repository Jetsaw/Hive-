from __future__ import annotations

from typing import Any

import faiss

from app.agents.trace import Trace
from app.rag import retriever
from app.rag.rag_metrics import RAGMetrics


class RetrieverAgent:
    def retrieve(
        self,
        index: faiss.Index | None,
        metas: list[dict] | None,
        query: str,
        trace: Trace,
        top_k: int | None = None,
        use_reranking: bool = False,
        metadata_filter: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        results = retriever.search(
            index, 
            metas or [], 
            query, 
            top_k=top_k,
            metadata_filter=metadata_filter,
            use_reranking=use_reranking
        )
        context, sources = retriever.build_context(results)
        
        # Compute RAG metrics
        metrics = RAGMetrics.compute_all_metrics(results, top_k=top_k or 3)

        output = {
            "context": context,
            "sources": sources,
            "result_count": len(results),
        }
        trace.add(
            name="retriever",
            input_data={
                "query": query, 
                "top_k": top_k,
                "use_reranking": use_reranking,
                "metadata_filter": metadata_filter,
            },
            output_data=output,
            metadata={
                "has_index": bool(index and index.ntotal),
                "metrics": metrics,
            },
        )
        return output
