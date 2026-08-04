"""
LOF Anomaly Detector — ForenSight AI
Local Outlier Factor — catches local density anomalies.
Architecture Section 5.5.2.
"""

import numpy as np
from backend.app.services.intelligence.anomaly.base import BaseAnomalyModel, AnomalyResult


class LOFModel(BaseAnomalyModel):
    name = "lof"

    def fit_predict(self, X: np.ndarray) -> AnomalyResult:
        from sklearn.neighbors import LocalOutlierFactor
        n = len(X)
        if n == 0:
            return AnomalyResult(model=self.name, flags=[], scores=[])

        # Cap at 300 samples for LOF to prevent O(n^2) memory spikes on 512MB RAM
        X_sub = X[:300] if n > 300 else X
        n_sub = len(X_sub)
        n_neighbors = min(10, n_sub - 1) if n_sub > 1 else 1

        model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=0.05,
            algorithm="ball_tree",
            leaf_size=30,
            n_jobs=1,  # Single-threaded low RAM
        )
        preds_sub = model.fit_predict(X_sub)
        raw_sub = -model.negative_outlier_factor_

        mn, mx = raw_sub.min(), raw_sub.max()
        scores_sub = ((raw_sub - mn) / (mx - mn)).tolist() if mx > mn else [0.0] * n_sub
        flags_sub = (preds_sub == -1).tolist()

        if n > 300:
            scores = scores_sub + [0.0] * (n - 300)
            flags = flags_sub + [False] * (n - 300)
        else:
            scores = scores_sub
            flags = flags_sub
        return AnomalyResult(model=self.name, flags=flags, scores=scores)
