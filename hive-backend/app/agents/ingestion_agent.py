from __future__ import annotations

from typing import Any

import faiss

from app.agents.trace import Trace
from app.rag.indexer import build_or_load_global_index


class IngestionAgent:
    def build_or_load(self, trace: Trace) -> tuple[faiss.Index, list[dict]]:
        index, metas = build_or_load_global_index()
        trace.add(
            name="ingestion",
            input_data={"action": "build_or_load_global_index"},
            output_data={"index_size": int(index.ntotal), "meta_count": len(metas)},
        )
        return index, metas
