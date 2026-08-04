from sklearn.svm import OneClassSVM as SkSVM
import numpy as np

class OneClassSVMOutlier:
    def __init__(self, nu=0.05, kernel="rbf", gamma="scale"):
        self.model = SkSVM(nu=nu, kernel=kernel, gamma=gamma)

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.fit_predict(X)
