"""KMeans segmentation of Dubai areas into investment tiers.

Clusters areas on development activity, delivery reliability, and maturity, then
orders the clusters by a composite quality score and labels them Tier 1 (best)
to Tier N. The result powers the District Intelligence dashboard page.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from ..analysis.projects_analysis import area_summary

_FEATURES = ["n_projects", "total_units", "avg_completion",
             "ready_rate", "n_developers", "delivery_rate"]


def segment_areas(projects: pd.DataFrame, k: int = 4, seed: int = 42) -> pd.DataFrame:
    areas = area_summary(projects).copy()
    feats = areas[_FEATURES].fillna(0.0)

    X = StandardScaler().fit_transform(feats)
    km = KMeans(n_clusters=k, random_state=seed, n_init=10)
    areas["cluster"] = km.fit_predict(X)

    # Composite quality score to rank clusters into ordered tiers.
    # Quality first: delivery reliability and completion dominate the ordering,
    # with development scale a minor tie-breaker, so Tier 1 = most investable.
    score = (
        0.40 * areas["delivery_rate"].rank(pct=True)
        + 0.35 * areas["avg_completion"].rank(pct=True)
        + 0.15 * areas["ready_rate"].rank(pct=True)
        + 0.10 * np.log1p(areas["total_units"]).rank(pct=True)
    )
    cluster_rank = (
        score.groupby(areas["cluster"]).mean().sort_values(ascending=False)
    )
    tier_map = {c: f"Tier {i+1}" for i, c in enumerate(cluster_rank.index)}
    areas["investment_tier"] = areas["cluster"].map(tier_map)
    areas["tier_rank"] = areas["investment_tier"].str.extract(r"(\d+)").astype(int)
    return areas.sort_values(["tier_rank", "n_projects"], ascending=[True, False]).reset_index(drop=True)
