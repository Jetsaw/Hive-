from __future__ import annotations

from typing import Any

import faiss

from app.agents.trace import Trace
from app.rag import retriever


class RetrieverAgent:
    def retrieve(
        self,
        index: faiss.Index | None,
        metas: list[dict] | None,
        query: str,
        trace: Trace,
        top_k: int | None = None,
    ) -> dict[str, Any]:
        results = retriever.search(index, metas or [], query, top_k=top_k)
        context, sources = retriever.build_context(results)

        output = {
            "context": context,
            "sources": sources,
            "result_count": len(results),
        }
        trace.add(
            name="retriever",
            input_data={"query": query, "top_k": top_k},
            output_data=output,
            metadata={"has_index": bool(index and index.ntotal)},
        )
        return output
