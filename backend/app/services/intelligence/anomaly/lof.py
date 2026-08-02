"""
LOF Anomaly Detector — ForenSight AI
Local Outlier Factor — catches local density anomalies.
Architecture Section 5.5.2.
"""

import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from backend.app.services.intelligence.anomaly.base import BaseAnomalyModel, AnomalyResult


class LOFModel(BaseAnomalyModel):
    name = "lof"

    def fit_predict(self, X: np.ndarray) -> AnomalyResult:
        n = len(X)
        # Keep neighbors small — LOF is O(n * k) with ball_tree; large k is very slow
        n_neighbors = min(10, n - 1) if n > 1 else 1
        model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=0.05,
            algorithm="ball_tree",   # ball_tree is faster than brute for n>200
            leaf_size=40,
            n_jobs=-1,               # use all CPU cores
        )
        preds = model.fit_predict(X)          # 1=inlier, -1=outlier

        # LOF scores are negative — more negative = more anomalous
        raw = -model.negative_outlier_factor_
        mn, mx = raw.min(), raw.max()
        scores = ((raw - mn) / (mx - mn)).tolist() if mx > mn else [0.0] * n
        flags = (preds == -1).tolist()
        return AnomalyResult(model=self.name, flags=flags, scores=scores)
