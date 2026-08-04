import os
from sentence_transformers import SentenceTransformer

_minilm_model = None

class MiniLMEmbedder:
    def __init__(self):
        global _minilm_model
        if _minilm_model is None:
            # point to backend/app/.cache
            cache_folder = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 
                ".cache"
            )
            # Enforce local_files_only=True to prevent network calls
            _minilm_model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=cache_folder, local_files_only=True)
        self.model = _minilm_model

    def encode(self, sentences: list):
        return self.model.encode(sentences)

def get_embedder():
    return MiniLMEmbedder()
