from sklearn.neighbors import LocalOutlierFactor as SkLOF
import numpy as np

class LocalOutlierFactorOutlier:
    def __init__(self, contamination=0.05):
        # Set novelty=False for standard unsupervised training set anomaly marking
        self.model = SkLOF(
            n_neighbors=15,
            contamination=contamination,
            novelty=False
        )

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.fit_predict(X)
