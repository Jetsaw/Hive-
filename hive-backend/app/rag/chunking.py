from dataclasses import dataclass

@dataclass
class Chunk:
    text: str
    meta: dict


def simple_chunk(text: str, meta: dict, chunk_size: int = 1200, overlap: int = 200) -> list[Chunk]:
    text = (text or "").strip()
    if not text:
        return []

    out: list[Chunk] = []
    i = 0
    n = len(text)
    while i < n:
        j = min(n, i + chunk_size)
        chunk_text = text[i:j].strip()
        if chunk_text:
            out.append(Chunk(text=chunk_text, meta=dict(meta)))
        if j >= n:
            break
        i = max(0, j - overlap)
    return out
