"""
One-Class SVM Anomaly Detector — ForenSight AI
Works well with small, high-dimensional forensic datasets.
Architecture Section 5.5.2.
"""

import numpy as np
from backend.app.services.intelligence.anomaly.base import BaseAnomalyModel, AnomalyResult


class OneClassSVMModel(BaseAnomalyModel):
    name = "oneclass_svm"

    def fit_predict(self, X: np.ndarray) -> AnomalyResult:
        from sklearn.svm import OneClassSVM
        from sklearn.preprocessing import StandardScaler
        n = len(X)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        nu = 0.05 if n >= 20 else 0.1
        model = OneClassSVM(nu=nu, kernel="rbf", gamma="scale")
        preds = model.fit_predict(X_scaled)   # 1=inlier, -1=outlier

        raw = -model.decision_function(X_scaled)   # higher = more anomalous
        mn, mx = raw.min(), raw.max()
        scores = ((raw - mn) / (mx - mn)).tolist() if mx > mn else [0.0] * n
        flags = (preds == -1).tolist()
        return AnomalyResult(model=self.name, flags=flags, scores=scores)
