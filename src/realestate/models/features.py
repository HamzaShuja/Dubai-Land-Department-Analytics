"""Feature engineering for the project-delivery model.

The model predicts a project's **eventual completion percentage** — a proxy for
delivery risk that an off-plan investor cares about most. Features deliberately
exclude the project's own status / delivery flags (which would leak the target).
Developer-level reputation signals are encoded with a **leave-one-out** mean so
a project never sees its own outcome inside its aggregate features.

The feature set is intentionally developer-centric (no area/community inputs):
a prediction only requires the developer plus the project's own attributes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TARGET = "percent_completed"

NUMERIC_FEATURES = [
    "no_of_units", "no_of_buildings", "no_of_villas", "no_of_lands",
    "total_assets", "planned_duration_days", "start_year",
    "dev_n_projects", "dev_total_units", "dev_delivered_rate_loo",
    "dev_avg_completion_loo", "project_type_code",
]


def _loo_mean(df: pd.DataFrame, key: str, value: str) -> pd.Series:
    """Leave-one-out group mean of ``value`` within ``key``."""
    grp = df.groupby(key)[value]
    g_sum = grp.transform("sum")
    g_cnt = grp.transform("count")
    loo = (g_sum - df[value]) / (g_cnt - 1).replace(0, np.nan)
    return loo.fillna(df[value].mean())


def build_features(projects: pd.DataFrame) -> tuple[pd.DataFrame, list[str], str]:
    df = projects.copy()

    # Numeric target/value helpers
    df["delivered_num"] = df["is_delivered"].astype(float)

    # Developer-level signals (leave-one-out to avoid target leakage)
    df["dev_delivered_rate_loo"] = _loo_mean(df, "developer_name", "delivered_num") * 100.0
    df["dev_avg_completion_loo"] = _loo_mean(df, "developer_name", "percent_completed")
    df["dev_n_projects"] = df.groupby("developer_name")["project_id"].transform("count")
    df["dev_total_units"] = df.groupby("developer_name")["no_of_units"].transform("sum")

    # Categorical encoding for project type
    df["project_type_code"] = df["project_type"].astype("category").cat.codes

    # Impute remaining numeric gaps with column medians
    for col in NUMERIC_FEATURES:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

    return df, NUMERIC_FEATURES, TARGET
