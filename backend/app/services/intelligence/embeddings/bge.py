import os
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
_bge_model = None

class BGEEmbedder:
    def __init__(self):
        global _bge_model
        if _bge_model is None:
            # point to backend/app/.cache
            cache_folder = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 
                ".cache"
            )
            # Use local cached all-MiniLM-L6-v2 directly to guarantee offline efficiency
            _bge_model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=cache_folder, local_files_only=True)
        self.model = _bge_model

    def encode(self, sentences: list):
        return self.model.encode(sentences)

def get_embedder():
    return BGEEmbedder()
