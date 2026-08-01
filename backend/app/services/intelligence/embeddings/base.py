"""Base embedding model contract."""

from abc import ABC, abstractmethod
from typing import List
import numpy as np


class BaseEmbeddingModel(ABC):
    model_name: str = "base"

    @abstractmethod
    def encode(self, texts: List[str]) -> np.ndarray:
        """Return (N, D) float32 embedding matrix."""

    @property
    def dimension(self) -> int:
        """Return embedding dimension (must be set after model load)."""
        raise NotImplementedError
