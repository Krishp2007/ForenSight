from .minilm import get_embedder as get_minilm
from .bge import get_embedder as get_bge
from .e5 import get_embedder as get_e5
from .evaluator import EmbeddingsEvaluator

def get_embedder(model_name: str):
    """Retrieve corresponding sentence-transformer embedding model by provider name."""
    name = model_name.lower()
    if "minilm" in name:
        return get_minilm()
    elif "bge" in name:
        return get_bge()
    elif "e5" in name:
        return get_e5()
    return get_minilm()
