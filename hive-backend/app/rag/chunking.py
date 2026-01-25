import re
from dataclasses import dataclass

@dataclass
class Chunk:
    text: str
    meta: dict


class RecursiveCharacterTextSplitter:
    # Sentence ending patterns for better boundary detection
    SENTENCE_ENDINGS = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, separators: list[str] | None = None, use_sentence_boundaries: bool = True):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._use_sentence_boundaries = use_sentence_boundaries
        # Improved separator hierarchy: paragraphs → sentences → phrases → words → characters
        self._separators = separators or ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]

    def _split_by_sentences(self, text: str) -> list[str]:
        """Split text by sentence boundaries using regex."""
        sentences = self.SENTENCE_ENDINGS.split(text)
        return [s.strip() for s in sentences if s.strip()]
    
    def split_text(self, text: str) -> list[str]:
        final_chunks = []
        
        # If sentence boundary mode, try sentence splitting first for better semantic preservation
        if self._use_sentence_boundaries and len(text) > self._chunk_size:
            # Try splitting by sentences first
            sentences = self._split_by_sentences(text)
            if len(sentences) > 1:
                return self._merge_splits(sentences, " ")
        
        # Fall back to separator-based splitting
        separator = self._separators[-1]
        
        # Find the best separator to use
        for sep in self._separators:
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                break
                
        # Split
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)  # atomic characters

        return self._merge_splits(splits, separator)
    
    def _merge_splits(self, splits: list[str], separator: str) -> list[str]:
        """Merge splits into chunks with overlap."""
        final_chunks = []
        _separator = separator if separator else ""
        
        current_chunk = []
        current_length = 0
        
        for s in splits:
            if not s:  # Skip empty splits
                continue
                
            s_len = len(s)
            potential_length = current_length + s_len + (len(_separator) if current_chunk else 0)
            
            if potential_length > self._chunk_size:
                if current_chunk:
                    # Save current chunk
                    doc = _separator.join(current_chunk)
                    final_chunks.append(doc)
                    
                    # Maintain overlap: keep trailing elements that fit in overlap window
                    while current_length > self._chunk_overlap and len(current_chunk) > 1:
                        popped = current_chunk.pop(0)
                        current_length -= (len(popped) + len(_separator))
                    
                    # If single split is larger than chunk_size, add it as its own chunk
                    if not current_chunk and s_len > self._chunk_size:
                        final_chunks.append(s)
                        current_chunk = []
                        current_length = 0
                        continue
                
                # Start new chunk or add to overlap
                if not current_chunk:
                    current_chunk = [s]
                    current_length = s_len
                else:
                    current_chunk.append(s)
                    current_length += s_len + len(_separator)
            else:
                current_chunk.append(s)
                current_length += s_len + (len(_separator) if len(current_chunk) > 1 else 0)
                
        if current_chunk:
            final_chunks.append(_separator.join(current_chunk))
            
        return final_chunks


def simple_chunk(text: str, meta: dict, chunk_size: int = 1000, overlap: int = 200) -> list[Chunk]:
    """
    Uses recursive splitting to respect semantic boundaries.
    """
    text = (text or "").strip()
    if not text:
        return []

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    texts = splitter.split_text(text)
    
    return [Chunk(text=t, meta=dict(meta)) for t in texts]
