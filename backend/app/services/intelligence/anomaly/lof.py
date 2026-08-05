"""
LOF Anomaly Detector — ForenSight AI
Local Outlier Factor — catches local density anomalies.
Architecture Section 5.5.2.

Fix applied: Variance check before fitting.
Browser history events produce near-constant feature vectors
(all visits by 'ChromeProcess' at similar hours) which causes
LOF to fail with 'duplicate points' warnings. Features with
zero variance are dropped before fitting.
"""

import logging
import numpy as np
from backend.app.services.intelligence.anomaly.base import BaseAnomalyModel, AnomalyResult

logger = logging.getLogger(__name__)


class LOFModel(BaseAnomalyModel):
    name = "lof"

    def fit_predict(self, X: np.ndarray) -> AnomalyResult:
        from sklearn.neighbors import LocalOutlierFactor
        n = len(X)
        if n == 0:
            return AnomalyResult(model=self.name, flags=[], scores=[])

        # Cap at 300 samples for LOF to prevent O(n^2) memory spikes on 512MB RAM
        X_sub = X[:300] if n > 300 else X
        n_sub = len(X_sub)

        # ── Variance check: drop zero-variance features ───────────────────────
        # Browser history events often have identical subject/action/hour columns.
        # LOF with zero-variance features degenerates and produces warnings.
        col_variance = np.var(X_sub, axis=0)
        non_constant_cols = np.where(col_variance > 1e-10)[0]

        if len(non_constant_cols) == 0:
            # ALL features are constant — no basis for outlier detection.
            # Return neutral scores (no anomalies via LOF).
            logger.info(
                f"[LOF] All {X_sub.shape[1]} features have zero variance "
                f"(n={n_sub}) — skipping LOF, returning neutral scores."
            )
            scores = [0.0] * n
            flags = [False] * n
            return AnomalyResult(model=self.name, flags=flags, scores=scores)

        if len(non_constant_cols) < X_sub.shape[1]:
            dropped = X_sub.shape[1] - len(non_constant_cols)
            logger.info(
                f"[LOF] Dropped {dropped} zero-variance feature(s) out of {X_sub.shape[1]} "
                f"(n={n_sub}). Fitting on {len(non_constant_cols)} informative feature(s)."
            )
            X_sub_filtered = X_sub[:, non_constant_cols]
        else:
            X_sub_filtered = X_sub

        # ── Adaptive n_neighbors based on unique feature vectors ──────────────
        # LOF requires n_neighbors < number of unique feature vectors.
        unique_rows = len(np.unique(X_sub_filtered, axis=0))
        # n_neighbors must be < n_sub AND < unique_rows
        max_neighbors = min(n_sub - 1, unique_rows - 1) if unique_rows > 1 else 1
        n_neighbors = min(10, max_neighbors) if max_neighbors >= 1 else 1

        if n_neighbors < 2:
            # Insufficient unique points for meaningful LOF
            logger.info(
                f"[LOF] Too few unique feature vectors ({unique_rows}) for LOF "
                f"(n={n_sub}) — returning neutral scores."
            )
            scores = [0.0] * n
            flags = [False] * n
            return AnomalyResult(model=self.name, flags=flags, scores=scores)

        model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=0.05,
            algorithm="ball_tree",
            leaf_size=30,
            n_jobs=1,  # Single-threaded low RAM
        )

        try:
            preds_sub = model.fit_predict(X_sub_filtered)
            raw_sub = -model.negative_outlier_factor_
        except Exception as lof_err:
            logger.warning(f"[LOF] fit_predict failed ({lof_err}) — returning neutral scores.")
            scores = [0.0] * n
            flags = [False] * n
            return AnomalyResult(model=self.name, flags=flags, scores=scores)

        mn, mx = raw_sub.min(), raw_sub.max()
        scores_sub = ((raw_sub - mn) / (mx - mn)).tolist() if mx > mn else [0.0] * n_sub
        flags_sub = (preds_sub == -1).tolist()

        if n > 300:
            scores = scores_sub + [0.0] * (n - 300)
            flags = flags_sub + [False] * (n - 300)
        else:
            scores = scores_sub
            flags = flags_sub

        logger.info(
            f"[LOF] n={n_sub}, unique_rows={unique_rows}, "
            f"n_neighbors={n_neighbors}, features={len(non_constant_cols)}, "
            f"flagged={sum(flags_sub)}"
        )
        return AnomalyResult(model=self.name, flags=flags, scores=scores)
