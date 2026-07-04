"""Isolation Forest anomaly detection.

Two surfaces:

* ``detect_transaction_anomalies`` – flags unusual quarter/property-type market
  observations (e.g. a quarter where average value per transaction or volume
  departs sharply from the historical pattern).
* ``detect_project_anomalies`` – flags projects whose size / completion /
  duration profile is atypical, surfacing potential data-quality issues or
  genuinely unusual developments.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from .market import transaction_summary


def _fit_flags(X: pd.DataFrame, contamination: float, seed: int = 42):
    Xf = X.replace([np.inf, -np.inf], np.nan).fillna(X.median(numeric_only=True))
    model = IsolationForest(
        n_estimators=200, contamination=contamination, random_state=seed
    )
    labels = model.fit_predict(Xf)              # -1 anomaly, 1 normal
    scores = model.score_samples(Xf)            # lower = more anomalous
    return labels, scores, model


def detect_transaction_anomalies(tx: pd.DataFrame, group: str = "Sales",
                                 contamination: float = 0.05) -> pd.DataFrame:
    s = transaction_summary(tx)
    s = s[s["transaction_group"] == group].copy()
    feats = s[["value_aed", "count", "avg_value_per_txn"]]
    labels, scores, _ = _fit_flags(feats, contamination)
    s["anomaly_score"] = scores
    s["is_anomaly"] = labels == -1
    return s.sort_values("anomaly_score").reset_index(drop=True)


def detect_project_anomalies(projects: pd.DataFrame,
                             contamination: float = 0.03) -> pd.DataFrame:
    df = projects.copy()
    feats = df[["percent_completed", "no_of_units", "total_assets",
                "planned_duration_days"]]
    labels, scores, _ = _fit_flags(feats, contamination)
    df["anomaly_score"] = scores
    df["is_anomaly"] = labels == -1
    cols = ["project_id", "master_project_en", "area_name_en", "developer_name",
            "project_status", "percent_completed", "no_of_units",
            "planned_duration_days", "anomaly_score", "is_anomaly"]
    cols = [c for c in cols if c in df.columns]  # tolerate older DB snapshots
    return df[cols].sort_values("anomaly_score").reset_index(drop=True)
