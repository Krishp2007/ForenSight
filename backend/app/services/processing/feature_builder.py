import numpy as np
from typing import List, Dict, Any
from collections import Counter
from datetime import datetime

SEVERITY_MAP = {
    "info": 0.0,
    "low": 0.25,
    "medium": 0.5,
    "high": 0.75,
    "critical": 1.0
}

class ForensicFeatureBuilder:
    @classmethod
    def extract_features_matrix(cls, events: List[Dict[str, Any]]) -> np.ndarray:
        """Convert a list of normalized events into a numerical 6-dimensional feature matrix for ML models."""
        total = len(events)
        if total == 0:
            return np.empty((0, 6))

        subjects = [str(e.get("subject", "")).lower() for e in events]
        actions = [str(e.get("action", "")).lower() for e in events]
        objects = [str(e.get("object", "")).lower() for e in events]

        subj_counts = Counter(subjects)
        act_counts = Counter(actions)
        obj_counts = Counter(objects)

        matrix = []
        for e in events:
            # 1. Resolve hour
            ts = e.get("timestamp")
            if isinstance(ts, datetime):
                hour = float(ts.hour)
                is_weekend = 1.0 if ts.weekday() >= 5 else 0.0
            else:
                hour = 12.0
                is_weekend = 0.0

            # 2-4. Category frequency ratios
            subj_freq = float(subj_counts[str(e.get("subject", "")).lower()] / total)
            act_freq = float(act_counts[str(e.get("action", "")).lower()] / total)
            obj_freq = float(obj_counts[str(e.get("object", "")).lower()] / total)

            # 5. Severity weights mapping
            sev = str(e.get("severity", "info")).lower()
            sev_val = float(SEVERITY_MAP.get(sev, 0.0))

            matrix.append([
                hour,
                is_weekend,
                subj_freq,
                obj_freq,
                act_freq,
                sev_val
            ])

        return np.array(matrix)
