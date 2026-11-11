"""
PharmaMind AI - Swappable Vector Storage Implementation
Implements FAISS IndexFlatIP and high-performance pure-Numpy vector stores.
"""

from typing import List, Dict, Any, Optional
import logging
import numpy as np
from app.services.semantic_search.base import BaseVectorStore

logger = logging.getLogger("pharmamind.services.semantic_search")


class NumpyVectorStore(BaseVectorStore):
    """
    High-performance exact vector index powered by NumPy.
    Computes inner-product / cosine similarity across normalized embeddings with zero external C++ dependencies.
    """

    def __init__(self, dimension: int = 384):
        self._dimension = dimension
        self._documents: List[Dict[str, Any]] = []
        self._embeddings: np.ndarray = np.empty((0, dimension), dtype=np.float32)

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def total_documents(self) -> int:
        return len(self._documents)

    def add_documents(self, documents: List[Dict[str, Any]], embeddings: np.ndarray) -> None:
        """Add documents and corresponding normalized embeddings."""
        if len(documents) == 0:
            return

        if embeddings.shape[1] != self._dimension:
            raise ValueError(f"Embedding dimension {embeddings.shape[1]} does not match index dimension {self._dimension}")

        # Ensure float32 and L2 normalization
        normalized_embs = embeddings.astype(np.float32)
        norms = np.linalg.norm(normalized_embs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized_embs /= norms

        if self._embeddings.shape[0] == 0:
            self._embeddings = normalized_embs
        else:
            self._embeddings = np.vstack([self._embeddings, normalized_embs])

        self._documents.extend(documents)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search Top-K nearest neighbors via cosine similarity."""
        if self.total_documents == 0:
            return []

        # Normalize query vector
        q_vec = query_embedding.astype(np.float32).flatten()
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec /= q_norm

        # Vectorized dot product (cosine similarity for normalized vectors)
        scores = np.dot(self._embeddings, q_vec)

        # Apply metadata filters if provided
        candidate_indices = []
        for idx, doc in enumerate(self._documents):
            if filters:
                matches = all(doc.get(k) == v for k, v in filters.items())
                if not matches:
                    continue
            candidate_indices.append(idx)

        if not candidate_indices:
            return []

        # Sort candidate scores descending
        candidate_indices.sort(key=lambda i: scores[i], reverse=True)
        top_indices = candidate_indices[:top_k]

        results = []
        for idx in top_indices:
            doc_copy = dict(self._documents[idx])
            doc_copy["similarity_score"] = float(round(scores[idx], 4))
            results.append(doc_copy)

        return results

    def clear(self) -> None:
        """Clear all stored documents and embeddings."""
        self._documents.clear()
        self._embeddings = np.empty((0, self._dimension), dtype=np.float32)


class FaissVectorStore(BaseVectorStore):
    """
    FAISS-powered vector store using IndexFlatIP for exact maximum inner product search.
    """

    def __init__(self, dimension: int = 384):
        self._dimension = dimension
        self._documents: List[Dict[str, Any]] = []
        try:
            import faiss
            self._faiss = faiss
            self._index = faiss.IndexFlatIP(dimension)
            self._is_available = True
        except ImportError:
            self._faiss = None
            self._index = None
            self._is_available = False

    @property
    def is_available(self) -> bool:
        return self._is_available

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def total_documents(self) -> int:
        return len(self._documents)

    def add_documents(self, documents: List[Dict[str, Any]], embeddings: np.ndarray) -> None:
        if not self._is_available:
            raise RuntimeError("FAISS is not installed. Use NumpyVectorStore instead.")

        normalized_embs = embeddings.astype(np.float32)
        norms = np.linalg.norm(normalized_embs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized_embs /= norms

        self._index.add(normalized_embs)
        self._documents.extend(documents)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if not self._is_available:
            raise RuntimeError("FAISS is not installed.")

        q_vec = query_embedding.astype(np.float32).reshape(1, -1)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec /= q_norm

        k_fetch = min(top_k * 4 if filters else top_k, self.total_documents)
        if k_fetch <= 0:
            return []

        distances, indices = self._index.search(q_vec, k_fetch)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._documents):
                continue
            doc = self._documents[idx]
            if filters:
                if not all(doc.get(k) == v for k, v in filters.items()):
                    continue
            doc_copy = dict(doc)
            doc_copy["similarity_score"] = float(round(dist, 4))
            results.append(doc_copy)
            if len(results) >= top_k:
                break

        return results

    def clear(self) -> None:
        if self._is_available:
            self._index = self._faiss.IndexFlatIP(self._dimension)
        self._documents.clear()


def create_vector_store(dimension: int = 384, prefer_faiss: bool = True) -> BaseVectorStore:
    """
    Factory function: returns FaissVectorStore if faiss is available, else NumpyVectorStore.
    """
    if prefer_faiss:
        try:
            store = FaissVectorStore(dimension=dimension)
            if store.is_available:
                return store
        except Exception:
            pass

    return NumpyVectorStore(dimension=dimension)

