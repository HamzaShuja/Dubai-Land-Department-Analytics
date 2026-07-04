"""Project- and area-level analysis from the DLD projects dataset."""
from __future__ import annotations

import numpy as np
import pandas as pd


def area_summary(projects: pd.DataFrame) -> pd.DataFrame:
    """Per-area development profile used by the geospatial map and segmentation."""
    g = projects.groupby("area_name_en")
    out = pd.DataFrame({
        "n_projects": g.size(),
        "total_units": g["no_of_units"].sum(),
        "avg_completion": g["percent_completed"].mean(),
        "ready_rate": g["is_ready"].mean() * 100.0,
        "offplan_rate": g["is_offplan"].mean() * 100.0,
        "n_developers": g["developer_name"].nunique(),
        "avg_duration_days": g["planned_duration_days"].mean(),
    }).reset_index()
    out["delivery_rate"] = g["is_delivered"].mean().values * 100.0
    return out.sort_values("n_projects", ascending=False).reset_index(drop=True)


def offplan_vs_ready(projects: pd.DataFrame) -> pd.DataFrame:
    """Side-by-side comparison of off-plan vs ready inventory."""
    rows = []
    for label, mask in [("Off-plan", projects["is_offplan"]),
                        ("Ready", projects["is_ready"])]:
        sub = projects[mask]
        rows.append({
            "segment": label,
            "n_projects": len(sub),
            "total_units": int(sub["no_of_units"].sum()),
            "avg_completion": round(sub["percent_completed"].mean(), 2),
            "avg_units_per_project": round(sub["no_of_units"].mean(), 1),
            "avg_duration_days": round(sub["planned_duration_days"].mean(), 1),
        })
    return pd.DataFrame(rows)
