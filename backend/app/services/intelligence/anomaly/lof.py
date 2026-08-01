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
        n_neighbors = min(20, n - 1) if n > 1 else 1
        model = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=0.05)
        preds = model.fit_predict(X)          # 1=inlier, -1=outlier

        # LOF scores are negative — more negative = more anomalous
        raw = -model.negative_outlier_factor_
        mn, mx = raw.min(), raw.max()
        scores = ((raw - mn) / (mx - mn)).tolist() if mx > mn else [0.0] * n
        flags = (preds == -1).tolist()
        return AnomalyResult(model=self.name, flags=flags, scores=scores)
