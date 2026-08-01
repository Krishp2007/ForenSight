"""
Isolation Forest Anomaly Detector — ForenSight AI
Architecture Section 5.5.2 — statistical / ML-based correlation.
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from backend.app.services.intelligence.anomaly.base import BaseAnomalyModel, AnomalyResult


class IsolationForestModel(BaseAnomalyModel):
    name = "isolation_forest"

    def fit_predict(self, X: np.ndarray) -> AnomalyResult:
        n = len(X)
        contamination = 0.05 if n >= 20 else "auto"
        model = IsolationForest(
            contamination=contamination, random_state=42, n_estimators=100
        )
        preds = model.fit_predict(X)          # 1=inlier, -1=outlier
        raw = model.decision_function(X)

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
