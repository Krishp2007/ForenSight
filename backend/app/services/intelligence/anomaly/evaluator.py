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
import time
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
        _t_model = time.perf_counter()
        try:
            result = model.fit_predict(X)
            all_flags[i] = [1 if f else 0 for f in result.flags]
            all_scores[i] = result.scores
            model_results[model.name] = result
            model_time = time.perf_counter() - _t_model
            logger.info(
                f"[PROFILE] ML {model.name:<20} {model_time:.3f}s  "
                f"(flagged {sum(result.flags)}/{n})"
            )
        except Exception as e:
            model_time = time.perf_counter() - _t_model
            logger.warning(f"[PROFILE] ML {model.name:<20} {model_time:.3f}s  FAILED: {e}")

    # Majority vote (≥2 of 3 models)
    _t_ensemble = time.perf_counter()
    vote_sum = all_flags.sum(axis=0)
    final_flags = (vote_sum >= 2).tolist()

    # Mean score
    final_scores = all_scores.mean(axis=0).tolist()
    ensemble_time = time.perf_counter() - _t_ensemble

    logger.info(
        f"[PROFILE] ML ensemble aggregation     {ensemble_time:.3f}s  "
        f"({sum(final_flags)}/{n} events flagged — models: {[m.name for m in MODELS]})"
    )

    return {
        "flags": final_flags,
        "scores": final_scores,
        "model_results": model_results,
    }
