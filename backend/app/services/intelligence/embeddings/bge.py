"""
BGE Embedding Provider — ForenSight AI
Architecture reference Section 6: "BAAI/bge-small-en-v1.5 — free, small, strong on retrieval."
"""

import os
import numpy as np
from typing import List

from backend.app.services.intelligence.embeddings.base import BaseEmbeddingModel

_CACHE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    ".cache",
)

_MODEL_NAME = "BAAI/bge-small-en-v1.5"


class BGEEmbedder(BaseEmbeddingModel):
    """
    BGE-small-en-v1.5 encoder.
    BGE models require a query instruction prefix for retrieval tasks.
    """

    model_name = _MODEL_NAME
    _model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self.__class__._model = SentenceTransformer(_MODEL_NAME, cache_folder=_CACHE)

    def encode(self, texts: List[str], is_query: bool = False) -> np.ndarray:
        """
        Encode texts. For retrieval queries, BGE recommends prepending
        "Represent this sentence for searching relevant passages: "
        """
        self._load()
        if is_query:
            texts = [
                f"Represent this sentence for searching relevant passages: {t}"
                for t in texts
            ]
        vecs = self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return vecs.astype("float32")

    @property
    def dimension(self) -> int:
        self._load()
        return self._model.get_sentence_embedding_dimension()
