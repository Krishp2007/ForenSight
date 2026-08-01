"""
HBOS Anomaly Detector — ForenSight AI
Histogram-Based Outlier Score via PyOD.
Architecture Section 5.5.2 — lightweight, fast on tabular forensic data.
"""

import numpy as np
from backend.app.services.intelligence.anomaly.base import BaseAnomalyModel, AnomalyResult


class HBOSModel(BaseAnomalyModel):
    name = "hbos"

    def fit_predict(self, X: np.ndarray) -> AnomalyResult:
        try:
            from pyod.models.hbos import HBOS
            n = len(X)
            contamination = 0.05 if n >= 20 else 0.1
            model = HBOS(contamination=contamination)
            model.fit(X)
            raw_scores = model.decision_scores_        # higher = more anomalous
            threshold = model.threshold_
            flags = (raw_scores >= threshold).tolist()

            mn, mx = raw_scores.min(), raw_scores.max()
            scores = ((raw_scores - mn) / (mx - mn)).tolist() if mx > mn else [0.0] * n
            return AnomalyResult(model=self.name, flags=flags, scores=scores)
        except ImportError:
            # pyod not installed — return all-normal result
            n = len(X)
            return AnomalyResult(model=self.name, flags=[False] * n, scores=[0.0] * n)
