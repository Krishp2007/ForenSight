"""
Base Anomaly Model — ForenSight AI
Shared contract for all anomaly detectors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
import numpy as np


@dataclass
class AnomalyResult:
    model: str
    flags: List[bool]       # True = anomaly
    scores: List[float]     # 0.0-1.0, higher = more anomalous


class BaseAnomalyModel(ABC):
    name: str = "base"

    @abstractmethod
    def fit_predict(self, X: np.ndarray) -> AnomalyResult:
        """Fit on X and return anomaly flags + scores."""
