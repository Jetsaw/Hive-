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
from app.rag.parsers.jsonl_parser import extract_jsonl

META_JSONL = "meta.jsonl"
INDEX_FAISS = "index.faiss"

# Layer-specific file names
STRUCTURE_INDEX = "structure_index.faiss"
STRUCTURE_META = "structure_meta.jsonl"
DETAILS_INDEX = "details_index.faiss"
DETAILS_META = "details_meta.jsonl"


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

            elif lower.endswith(".jsonl"):
                for text, metadata in extract_jsonl(p):
                    meta = {"source_file": fn, "path": p, "type": "jsonl"}
                    meta.update(metadata)  # Merge JSONL metadata
                    items.append((fn, text, meta))
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


def build_or_load_structure_index() -> tuple[faiss.Index, list[dict]]:
    """
    Build or load programme structure index.
    Handles programme_structure.jsonl for term planning and rules.
    """
    Path(settings.GLOBAL_INDEX_DIR).mkdir(parents=True, exist_ok=True)
    index_path = os.path.join(settings.GLOBAL_INDEX_DIR, STRUCTURE_INDEX)
    meta_path = os.path.join(settings.GLOBAL_INDEX_DIR, STRUCTURE_META)
    
    # Load if exists
    if os.path.exists(index_path) and os.path.exists(meta_path):
        index = faiss.read_index(index_path)
        metas: list[dict] = []
        with open(meta_path, "r", encoding="utf-8") as f:
            for line in f:
                metas.append(json.loads(line))
        return index, metas
    
    # Build from programme_structure.jsonl
    structure_file = os.path.join(settings.KB_DIR, "programme_structure.jsonl")
    
    if not os.path.exists(structure_file):
        # Return empty index
        dim = 384
        index = faiss.IndexFlatIP(dim)
        return index, []
    
    chunks = []
    with open(structure_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            
            # Create searchable text from question + answer (not 'content')
            question = data.get('question', '')
            answer = data.get('answer', '')
            text = f"Q: {question}\nA: {answer}"
            
            # Add metadata
            meta = {
                'id': data.get('id'),
                'type': data.get('type'),
                'programme': data.get('programme'),
                'term': data.get('term'),
                'question': question,
                'answer': answer,
                'layer': 'structure',
                'source_file': 'programme_structure.jsonl'
            }
            
            # Add course codes if present
            if 'course_codes' in data:
                meta['course_codes'] = data['course_codes']
            
            chunks.extend(simple_chunk(text, meta=meta))
    
    texts = [c.text for c in chunks]
    metas = [c.meta | {'text': c.text} for c in chunks]
    
    if not texts:
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


def build_or_load_details_index() -> tuple[faiss.Index, list[dict]]:
    """
    Build or load subject details index.
    Handles faie_ai_robotics_combined_qa.jsonl for course Q&A.
    """
    Path(settings.GLOBAL_INDEX_DIR).mkdir(parents=True, exist_ok=True)
    index_path = os.path.join(settings.GLOBAL_INDEX_DIR, DETAILS_INDEX)
    meta_path = os.path.join(settings.GLOBAL_INDEX_DIR, DETAILS_META)
    
    # Load if exists
    if os.path.exists(index_path) and os.path.exists(meta_path):
        index = faiss.read_index(index_path)
        metas: list[dict] = []
        with open(meta_path, "r", encoding="utf-8") as f:
            for line in f:
                metas.append(json.loads(line))
        return index, metas
    
    # Build from hive_course_qa_pairs.jsonl (new cleaned data)
    details_file = os.path.join(settings.KB_DIR, "hive_course_qa_pairs.jsonl")
    
    # Fallback to old file if new one doesn't exist
    if not os.path.exists(details_file):
        details_file = os.path.join(settings.KB_DIR, "faie_ai_robotics_combined_qa.jsonl")
    
    if not os.path.exists(details_file):
        # Return empty index
        dim = 384
        index = faiss.IndexFlatIP(dim)
        return index, []
    
    chunks = []
    with open(details_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            
            # Create searchable text from Q&A
            question = data.get('question', '')
            answer = data.get('answer', '')
            text = f"Q: {question}\nA: {answer}"
            
            # Add metadata
            meta = {
                'id': data.get('id'),
                'course_code': data.get('course_code'),
                'course_name': data.get('course_name'),
                'question': question,
                'answer': answer,
                'source': data.get('source', ''),  # Optional in new schema
                'layer': 'details',
                'source_file': os.path.basename(details_file)
            }
            
            # Add tags if present (new schema)
            if 'tags' in data:
                meta['tags'] = data['tags']
            
            chunks.extend(simple_chunk(text, meta=meta))
    
    texts = [c.text for c in chunks]
    metas = [c.meta | {'text': c.text} for c in chunks]
    
    if not texts:
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
