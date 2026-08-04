from typing import List, Dict, Any
import numpy as np
from sklearn.metrics import silhouette_score

from .isolation_forest import IsolationForestOutlier
from .lof import LocalOutlierFactorOutlier
from .oneclass_svm import OneClassSVMOutlier
from .hbos import HBOSOutlier

class AnomalyModelEvaluator:
    @staticmethod
    def compare_all(features: np.ndarray) -> List[Dict[str, Any]]:
        """Evaluate all anomaly detection models against a target feature matrix."""
        reports = []
        
        algorithms = {
            "isolation_forest": IsolationForestOutlier(contamination=0.05, random_state=42),
            "local_outlier_factor": LocalOutlierFactorOutlier(contamination=0.05),
            "one_class_svm": OneClassSVMOutlier(nu=0.05),
            "hbos": HBOSOutlier(contamination=0.05)
        }
        
        model_names = {
            "isolation_forest": "isolation_forest",
            "local_outlier_factor": "lof",
            "one_class_svm": "one_class_svm",
            "hbos": "hbos"
        }
        
        for key, model in algorithms.items():
            try:
                preds = model.fit_predict(features)
                inliers = int(np.sum(preds == 1))
                outliers = int(np.sum(preds == -1))
                
                # Check labels groups count to prevent silhouette exceptions
                unique_labels = len(np.unique(preds))
                if unique_labels > 1:
                    score = float(silhouette_score(features, preds))
                else:
                    score = 0.0
                    
                reports.append({
                    "algorithm": model_names.get(key, key),
                    "status": "success",
                    "inliers_count": inliers,
                    "outliers_count": outliers,
                    "silhouette_score": score
                })
            except Exception as e:
                reports.append({
                    "algorithm": model_names.get(key, key),
                    "status": "failed",
                    "error": str(e),
                    "inliers_count": 0,
                    "outliers_count": 0,
                    "silhouette_score": -1.0
                })
                
        return reports
