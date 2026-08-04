import os
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
_e5_model = None

class E5Embedder:
    def __init__(self):
        global _e5_model
        if _e5_model is None:
            # point to backend/app/.cache
            cache_folder = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 
                ".cache"
            )
            # Use local cached all-MiniLM-L6-v2 directly to guarantee offline efficiency
            _e5_model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=cache_folder, local_files_only=True)
        self.model = _e5_model

    def encode(self, sentences: list):
        formatted_sentences = [
            f"query: {s}" if not s.startswith("query:") and not s.startswith("passage:") else s 
            for s in sentences
        ]
        return self.model.encode(formatted_sentences)

def get_embedder():
    return E5Embedder()
