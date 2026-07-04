"""Developer reputation analysis from the DLD projects dataset.

Builds a per-developer scorecard: portfolio size, units delivered, delivery
rate, average completion, and a composite reputation score in [0, 100] that
blends delivery reliability with portfolio scale.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def developer_reputation(projects: pd.DataFrame, min_projects: int = 1) -> pd.DataFrame:
    g = projects.groupby("developer_name")
    rep = pd.DataFrame({
        "n_projects": g.size(),
        "total_units": g["no_of_units"].sum(),
        "avg_completion": g["percent_completed"].mean(),
        "delivered_rate": g["is_delivered"].mean() * 100.0,
        "ready_rate": g["is_ready"].mean() * 100.0,
        "avg_duration_days": g["planned_duration_days"].mean(),
        "n_areas": g["area_name_en"].nunique(),
    }).reset_index()

    rep = rep[rep["n_projects"] >= min_projects].copy()

    # Composite score: 60% delivery reliability, 25% avg completion,
    # 15% portfolio scale (log units, normalised).
    scale = np.log1p(rep["total_units"])
    scale_norm = (scale - scale.min()) / (scale.max() - scale.min() + 1e-9) * 100.0
    rep["reputation_score"] = (
        0.60 * rep["delivered_rate"]
        + 0.25 * rep["avg_completion"]
        + 0.15 * scale_norm
    ).round(2)
    return rep.sort_values("reputation_score", ascending=False).reset_index(drop=True)
