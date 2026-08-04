"""
Isolation Forest Anomaly Detector — ForenSight AI
===================================================
Production Inference Engine:
- Loads pre-trained model artifact ONCE per backend process.
- Performs fast inference (.decision_function / .predict) without re-training on upload.
"""

import os
import joblib
import logging
import numpy as np
from backend.app.services.intelligence.anomaly.base import BaseAnomalyModel, AnomalyResult

logger = logging.getLogger(__name__)

_GLOBAL_ISOLATION_FOREST_MODEL = None


def get_pretrained_model():
    """Load or initialize pre-trained Isolation Forest model ONCE in RAM."""
    global _GLOBAL_ISOLATION_FOREST_MODEL
    if _GLOBAL_ISOLATION_FOREST_MODEL is not None:
        return _GLOBAL_ISOLATION_FOREST_MODEL

    model_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "storage", "models", "isolation_forest.joblib"
    )

    if os.path.exists(model_path):
        try:
            _GLOBAL_ISOLATION_FOREST_MODEL = joblib.load(model_path)
            logger.info("Loaded pre-trained IsolationForest model artifact from disk.")
            return _GLOBAL_ISOLATION_FOREST_MODEL
        except Exception as e:
            logger.warning(f"Could not load pre-trained model ({e}), fallback to auto-fit.")

    # Fallback: Train once and save if file doesn't exist
    from backend.app.services.intelligence.anomaly.train_model import train_and_save_model
    train_and_save_model()
    _GLOBAL_ISOLATION_FOREST_MODEL = joblib.load(model_path)
    return _GLOBAL_ISOLATION_FOREST_MODEL


class IsolationForestModel(BaseAnomalyModel):
    name = "isolation_forest"

    def fit_predict(self, X: np.ndarray) -> AnomalyResult:
        n = len(X)
        if n == 0:
            return AnomalyResult(model=self.name, flags=[], scores=[])

        model = get_pretrained_model()

        # Fast Production Inference (0 re-training cost)
        try:
            raw = model.decision_function(X)
            preds = model.predict(X)
        except Exception:
            # If feature shape mismatch, fit lightweight fast tree in memory
            from sklearn.ensemble import IsolationForest
            fast_m = IsolationForest(n_estimators=30, max_samples=min(128, n), contamination=0.05, random_state=42, n_jobs=1)
            preds = fast_m.fit_predict(X)
            raw = fast_m.decision_function(X)

        mn, mx = raw.min(), raw.max()
        if mx - mn > 0:
            scores = 1.0 - ((raw - mn) / (mx - mn))
        else:
            scores = np.zeros(n)

        flags = (preds == -1).tolist()
        return AnomalyResult(
            model=self.name,
            flags=flags,
            scores=scores.tolist(),
        )
