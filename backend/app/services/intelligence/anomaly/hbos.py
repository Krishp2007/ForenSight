import numpy as np

class HBOSOutlier:
    def __init__(self, contamination=0.05):
        self.contamination = contamination

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """Fit HBOS model and return outlier predictions (-1 for outliers, 1 for inliers)."""
        n_samples, n_features = X.shape
        if n_samples == 0:
            return np.empty(0)
            
        scores = np.zeros(n_samples)
        
        for d in range(n_features):
            # Calculate 10 bins for each feature dimensions
            hist, bin_edges = np.histogram(X[:, d], bins=10)
            bin_indices = np.clip(np.digitize(X[:, d], bin_edges) - 1, 0, len(hist) - 1)
            
            # Normalize frequencies to densities
            freqs = hist[bin_indices] / n_samples
            
            # Avoid division by zero warnings or log(0) exceptions
            freqs = np.where(freqs == 0, 0.0001, freqs)
            scores += -np.log(freqs)
            
        # Classify based on contamination boundary threshold
        threshold = np.percentile(scores, 100 * (1 - self.contamination))
        preds = np.ones(n_samples)
        preds[scores > threshold] = -1
        
        return preds
