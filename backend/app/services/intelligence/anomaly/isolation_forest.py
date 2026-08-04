from sklearn.ensemble import IsolationForest as SkIsolationForest
import numpy as np

class IsolationForestOutlier:
    def __init__(self, contamination=0.05, random_state=42, n_estimators=100):
        # Handle 'auto' or numeric contamination parameter
        self.model = SkIsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=n_estimators
        )

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.fit_predict(X)
