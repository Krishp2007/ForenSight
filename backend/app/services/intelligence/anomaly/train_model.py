"""
Explicit ML Training Command — ForenSight AI
==============================================
Trains the Isolation Forest baseline anomaly model on synthetic/baseline security telemetry
and saves the trained model artifact to disk.

Usage:
  python -m backend.app.services.intelligence.anomaly.train_model
"""

import os
import joblib
import logging
import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "storage", "models"
)
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest.joblib")


def generate_baseline_dataset(samples: int = 1000) -> np.ndarray:
    """Generate representative baseline feature dataset for training."""
    np.random.seed(42)
    # Features: [hour (0-23), is_weekend (0/1), subj_freq (0-1), obj_freq (0-1), act_freq (0-1), severity_score (0-1)]
    hours = np.random.randint(8, 18, size=samples) # Mostly business hours
    weekend = np.random.choice([0, 1], size=samples, p=[0.85, 0.15])
    subj_freq = np.random.uniform(0.1, 0.9, size=samples)
    obj_freq = np.random.uniform(0.1, 0.9, size=samples)
    act_freq = np.random.uniform(0.1, 0.9, size=samples)
    sev = np.random.choice([0.0, 0.25, 0.5], size=samples, p=[0.7, 0.2, 0.1])

    return np.column_stack([hours, weekend, subj_freq, obj_freq, act_freq, sev])


def train_and_save_model() -> str:
    """Train Isolation Forest model artifact and persist to storage/models/."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    logger.info("Generating baseline training dataset...")
    X_train = generate_baseline_dataset(1200)

    logger.info("Fitting IsolationForest model artifact...")
    model = IsolationForest(
        n_estimators=50,
        max_samples=256,
        contamination=0.05,
        random_state=42,
        n_jobs=1,  # Single-threaded for low RAM footprint
    )
    model.fit(X_train)

    joblib.dump(model, MODEL_PATH, compress=3)
    logger.info(f"Successfully saved trained model artifact to {MODEL_PATH}")
    return MODEL_PATH


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_and_save_model()
