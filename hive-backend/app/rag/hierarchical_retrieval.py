from typing import List, Dict, Tuple
import faiss
import numpy as np
from app.rag.embeddings import embed_texts


class HierarchicalRetriever:
    """
    Implements hierarchical retrieval with multiple chunk sizes.
    First retrieves at coarse level, then refines at fine level.
    """
    
    def __init__(self):
        self.coarse_index: faiss.Index | None None
        self.fine_index: faiss.Index | None = None
        self.coarse_metas: List[Dict] = []
        self.fine_metas: List[Dict] = []
        self.parent_child_map: Dict[int, List[int]] = {}  # Maps coarse idx to fine indices
    
    def build_hierarchical_index(
        self,
        documents: List[str],
        coarse_chunk_size: int = 2000,
        fine_chunk_size: int = 500
    ) -> Tuple[faiss.Index, List[Dict], faiss.Index, List[Dict]]:
        """
        Build two-level hierarchical index.
        
        Args:
            documents: List of full documents
            coarse_chunk_size: Size for coarse chunks (e.g., sections)
            fine_chunk_size: Size for fine chunks (e.g., paragraphs)
        
        Returns:
            (coarse_index, coarse_metas, fine_index, fine_metas)
        """
        # This is a simplified implementation
        # In production, you'd use proper chunking strategies
        
        coarse_chunks = []
        fine_chunks = []
        coarse_metas = []
        fine_metas = []
        parent_child_map = {}
        
        for doc_idx, doc in enumerate(documents):
            # Create coarse chunks
            num_coarse = max(1, len(doc) // coarse_chunk_size)
            for i in range(num_coarse):
                start = i * coarse_chunk_size
                end = min((i + 1) * coarse_chunk_size, len(doc))
                coarse_chunk = doc[start:end]
                coarse_idx = len(coarse_chunks)
                coarse_chunks.append(coarse_chunk)
                coarse_metas.append({"doc_id": doc_idx, "chunk_id": i})
                
                # Create fine chunks within this coarse chunk
                child_indices = []
                num_fine = max(1, len(coarse_chunk) // fine_chunk_size)
                for j in range(num_fine):
                    fine_start = j * fine_chunk_size
                    fine_end = min((j + 1) * fine_chunk_size, len(coarse_chunk))
                    fine_chunk = coarse_chunk[fine_start:fine_end]
                    fine_idx = len(fine_chunks)
                    fine_chunks.append(fine_chunk)
                    fine_metas.append({"doc_id": doc_idx, "parent_chunk": coarse_idx, "fine_chunk_id": j})
                    child_indices.append(fine_idx)
                
                parent_child_map[coarse_idx] = child_indices
        
        # Build FAISS indices
        if coarse_chunks:
            coarse_vecs = embed_texts(coarse_chunks)
            coarse_index = faiss.IndexFlatIP(coarse_vecs.shape[1])
            coarse_index.add(coarse_vecs)
        else:
            coarse_index = faiss.IndexFlatIP(384)  # Default dimension
        
        if fine_chunks:
            fine_vecs = embed_texts(fine_chunks)
            fine_index = faiss.IndexFlatIP(fine_vecs.shape[1])
            fine_index.add(fine_vecs)
        else:
            fine_index = faiss.IndexFlatIP(384)
        
        self.coarse_index = coarse_index
        self.fine_index = fine_index
        self.coarse_metas = coarse_metas
        self.fine_metas = fine_metas
        self.parent_child_map = parent_child_map
        
        return coarse_index, coarse_metas, fine_index, fine_metas
    
    def hierarchical_search(
        self,
        query: str,
        coarse_top_k: int = 5,
        fine_top_k: int = 10
    ) -> List[Dict]:
        """
        Perform two-stage hierarchical search.
        
        Args:
            query: Search query
            coarse_top_k: Number of coarse chunks to retrieve
            fine_top_k: Number of fine chunks to retrieve per coarse chunk
        
        Returns:
            List of fine-grained results
        """
        if self.coarse_index is None or self.fine_index is None:
            return []
        
        from app.rag.embeddings import embed_query
        
        # Stage 1: Coarse retrieval
        q_vec = embed_query(query).reshape(1, -1)
        coarse_scores, coarse_ids = self.coarse_index.search(q_vec, coarse_top_k)
        
        # Stage 2: Fine retrieval within selected coarse chunks
        fine_results = []
        for coarse_idx in coarse_ids[0]:
            if coarse_idx == -1:
                continue
            
            # Get child fine chunks
            child_indices = self.parent_child_map.get(int(coarse_idx), [])
            if not child_indices:
                continue
            
            # Search within fine chunks (simplified - just return all children)
            for fine_idx in child_indices[:fine_top_k]:
                if fine_idx < len(self.fine_metas):
                    fine_results.append({
                        "idx": fine_idx,
                        "meta": self.fine_metas[fine_idx],
                        "score": 0.0  # Would compute actual relevance in production
                    })
        
        return fine_results[:fine_top_k * coarse_top_k]
