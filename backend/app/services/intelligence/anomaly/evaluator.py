"""
Anomaly Evaluator — ForenSight AI
====================================
Runs all three anomaly models, ensembles their scores by majority vote,
and returns a single unified result per event.

Architecture Section 5.5.2:
  "A clustering pass… A small classifier… None of this requires GPU."

Ensemble strategy:
  - An event is flagged as anomaly if ≥ 2 of 3 models flag it
  - Final score = mean of all model scores for that event
"""

import logging
import numpy as np
from typing import List, Dict, Any

from backend.app.services.intelligence.anomaly.base import AnomalyResult
from backend.app.services.intelligence.anomaly.isolation_forest import IsolationForestModel
from backend.app.services.intelligence.anomaly.hbos import HBOSModel
from backend.app.services.intelligence.anomaly.lof import LOFModel

logger = logging.getLogger(__name__)

MODELS = [IsolationForestModel(), HBOSModel(), LOFModel()]


def ensemble_predict(X: np.ndarray) -> Dict[str, Any]:
    """
    Run all models and ensemble the results.

    Returns
    -------
    {
      "flags":  [bool, ...],   # True if ≥2 models agree it's an anomaly
      "scores": [float, ...],  # mean score across models
      "model_results": { model_name: AnomalyResult }
    }
    """
    n = len(X)
    all_flags = np.zeros((len(MODELS), n), dtype=int)
    all_scores = np.zeros((len(MODELS), n), dtype=float)

    model_results: Dict[str, AnomalyResult] = {}

    for i, model in enumerate(MODELS):
        try:
            result = model.fit_predict(X)
            all_flags[i] = [1 if f else 0 for f in result.flags]
            all_scores[i] = result.scores
            model_results[model.name] = result
            logger.debug(
                f"[{model.name}] flagged {sum(result.flags)}/{n} events as anomalies"
            )
        except Exception as e:
            logger.warning(f"Model {model.name} failed: {e}. Skipping.")

    # Majority vote (≥2 of 3 models)
    vote_sum = all_flags.sum(axis=0)
    final_flags = (vote_sum >= 2).tolist()

    # Mean score
    final_scores = all_scores.mean(axis=0).tolist()

    logger.info(
        f"Ensemble: {sum(final_flags)}/{n} events flagged "
        f"({[m.name for m in MODELS]})"
    )

    return {
        "flags": final_flags,
        "scores": final_scores,
        "model_results": model_results,
    }
