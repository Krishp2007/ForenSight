"""
MiniLM Embedding Provider — ForenSight AI
Architecture reference: all-MiniLM-L6-v2 used for FAISS index.
"""

import os
import numpy as np
from typing import List

from backend.app.services.intelligence.embeddings.base import BaseEmbeddingModel

_CACHE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    ".cache",
)


class MiniLMEmbedder(BaseEmbeddingModel):
    model_name = "all-MiniLM-L6-v2"
    _model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self.__class__._model = SentenceTransformer(self.model_name, cache_folder=_CACHE)

    def encode(self, texts: List[str]) -> np.ndarray:
        self._load()
        return self._model.encode(texts, show_progress_bar=False).astype("float32")

    @property
    def dimension(self) -> int:
        self._load()
        return self._model.get_sentence_embedding_dimension()
