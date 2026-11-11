"""
PharmaMind AI - Vector Store Base Interface
Defines the swappable contract for vector storage, metadata indexing, and similarity retrieval.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np


class BaseVectorStore(ABC):
    """Abstract contract for dense vector indexing and Top-K retrieval."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensionality of the indexed vector space."""
        pass

    @property
    @abstractmethod
    def total_documents(self) -> int:
        """Total number of documents currently indexed."""
        pass

    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]], embeddings: np.ndarray) -> None:
        """
        Add documents with corresponding dense embeddings to the index.
        embeddings shape: (len(documents), dimension)
        """
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform Top-K nearest neighbor search with optional metadata filtering.
        query_embedding shape: (dimension,)
        Returns: List of document dicts with attached 'similarity_score'.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all indexed documents and embeddings."""
        pass

