import os
import json
from pathlib import Path
from typing import List, Dict, Tuple

import faiss

from app.core.config import settings
from app.rag.embeddings import embed_texts
from app.rag.chunking import simple_chunk
from app.rag.parsers.pdf import extract_pdf_pages
from app.rag.parsers.docx import extract_docx_text

META_JSONL = "meta.jsonl"
INDEX_FAISS = "index.faiss"


def _iter_global_docs(global_docs_dir: str) -> list[tuple[str, str, dict]]:
    """
    Returns list of (filename, text, meta)
    PDFs are split per page; DOCX is whole doc text.
    """
    items = []
    for root, _, files in os.walk(global_docs_dir):
        for fn in files:
            p = os.path.join(root, fn)
            lower = fn.lower()

            if lower.endswith(".pdf"):
                for page_no, page_text in extract_pdf_pages(p):
                    meta = {"source_file": fn, "path": p, "page": page_no, "type": "pdf"}
                    items.append((fn, page_text, meta))

            elif lower.endswith(".docx"):
                txt = extract_docx_text(p)
                meta = {"source_file": fn, "path": p, "type": "docx"}
                items.append((fn, txt, meta))
    return items


def build_or_load_global_index() -> tuple[faiss.Index, list[dict]]:
    Path(settings.GLOBAL_INDEX_DIR).mkdir(parents=True, exist_ok=True)
    index_path = os.path.join(settings.GLOBAL_INDEX_DIR, INDEX_FAISS)
    meta_path = os.path.join(settings.GLOBAL_INDEX_DIR, META_JSONL)

    # Load if exists
    if os.path.exists(index_path) and os.path.exists(meta_path):
        index = faiss.read_index(index_path)
        metas: list[dict] = []
        with open(meta_path, "r", encoding="utf-8") as f:
            for line in f:
                metas.append(json.loads(line))
        return index, metas

    # Build
    docs = _iter_global_docs(settings.GLOBAL_DOCS_DIR)

    chunks = []
    for _, text, meta in docs:
        # v1 scope: Intelligent Robotics only
        meta = dict(meta)
        meta["programme"] = "Intelligent Robotics"
        chunks.extend(simple_chunk(text, meta=meta))

    texts = [c.text for c in chunks]
    metas = [c.meta | {"text": c.text} for c in chunks]

    if not texts:
        # Empty index fallback (dims for MiniLM)
        dim = 384
        index = faiss.IndexFlatIP(dim)
    else:
        vecs = embed_texts(texts)
        dim = vecs.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(vecs)

    faiss.write_index(index, index_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        for m in metas:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    return index, metas
