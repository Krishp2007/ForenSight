"""
Embedding Evaluator — ForenSight AI
Compares MiniLM vs BGE on a small held-out set of case events
to select the best model for a given case's data distribution.
"""

import logging
import numpy as np
from typing import List, Tuple

from backend.app.services.intelligence.embeddings.minilm import MiniLMEmbedder
from backend.app.services.intelligence.embeddings.bge import BGEEmbedder

logger = logging.getLogger(__name__)


def _mean_reciprocal_rank(embeddings: np.ndarray, k: int = 5) -> float:
    """
    Approximate MRR using cosine self-similarity.
    Each vector is a query; its nearest neighbour (excluding itself) is the match.
    Higher MRR = better retrieval quality on this dataset.
    """
    n = len(embeddings)
    if n < 2:
        return 0.0

    # Normalise
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-9
    normed = embeddings / norms
    sim = normed @ normed.T
    np.fill_diagonal(sim, -1)  # exclude self

    mrr = 0.0
    for i in range(n):
        sorted_idx = np.argsort(-sim[i])[:k]
        # rank of the closest "semantically similar" doc (approximation)
        mrr += 1.0 / (sorted_idx[0] + 1)
    return mrr / n


def select_best_model(sample_texts: List[str]) -> str:
    """
    Encode sample_texts with both models and return the name of the
    one with the higher approximate MRR.

    Returns: "bge" | "minilm"
    """
    models = {
        "bge": BGEEmbedder(),
        "minilm": MiniLMEmbedder(),
    }
    best_name = "bge"   # default (architecture recommendation)
    best_mrr = -1.0

    for name, model in models.items():
        try:
            vecs = model.encode(sample_texts)
            mrr = _mean_reciprocal_rank(vecs)
            logger.info(f"[EmbEval] {name} MRR={mrr:.4f}")
            if mrr > best_mrr:
                best_mrr = mrr
                best_name = name
        except Exception as e:
            logger.warning(f"[EmbEval] {name} failed: {e}")

    logger.info(f"[EmbEval] Selected: {best_name} (MRR={best_mrr:.4f})")
    return best_name
