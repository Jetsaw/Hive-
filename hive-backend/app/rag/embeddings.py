import numpy as np
from sentence_transformers import SentenceTransformer

# Small + fast CPU model. No extra API keys needed.
_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def embed_texts(texts: list[str]) -> np.ndarray:
    vecs = _MODEL.encode(texts, normalize_embeddings=True)
    return np.asarray(vecs, dtype="float32")


def embed_query(text: str) -> np.ndarray:
    return embed_texts([text])[0]
