"""
PharmaMind AI - Base Embedding Interface
Defines the standard abstract contract for biomedical text representation and vectorization.
"""

from abc import ABC, abstractmethod
from typing import List, Union
import numpy as np


class BaseEmbeddingService(ABC):
    """Abstract contract for text embedding generation."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier of the active underlying model."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate a normalized 1D embedding vector for a single text input.
        Returns: np.ndarray of shape (dimension,) and dtype float32.
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate normalized embeddings for a batch of text inputs.
        Returns: np.ndarray of shape (len(texts), dimension) and dtype float32.
        """
        pass

