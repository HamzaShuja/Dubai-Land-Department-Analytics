"""Single-request inference and the developer reference table.

At training time we persist a compact reference table of developer-level
reputation features. At prediction time a request only needs the project's own
attributes plus its developer name; the matching reputation features are looked
up (falling back to global medians for unseen developers), assembled into the
exact feature vector the model expects, and scored. SHAP then attributes the
prediction to each input.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from ..config import PROJECT_ROOT
from .features import NUMERIC_FEATURES

REFERENCE_PATH = PROJECT_ROOT / "artifacts" / "models" / "reference.joblib"


def build_reference(projects: pd.DataFrame) -> dict:
    """Build developer reputation lookups + global fallbacks."""
    dev = projects.groupby("developer_name").agg(
        dev_delivered_rate_loo=("is_delivered", lambda s: s.mean() * 100.0),
        dev_avg_completion_loo=("percent_completed", "mean"),
        dev_n_projects=("project_id", "count"),
        dev_total_units=("no_of_units", "sum"),
    )
    type_cats = list(pd.Series(projects["project_type"].astype("category").cat.categories))
    _dated = projects.dropna(subset=["start_year"])
    year_median = (_dated.groupby(_dated["start_year"].astype(int))["percent_completed"]
                   .median().to_dict())
    globals_ = {
        "dev_delivered_rate_loo": float(projects["is_delivered"].mean() * 100.0),
        "dev_avg_completion_loo": float(projects["percent_completed"].mean()),
        "dev_n_projects": float(projects.groupby("developer_name").size().median()),
        "dev_total_units": float(projects.groupby("developer_name")["no_of_units"].sum().median()),
        "planned_duration_days": float(pd.to_numeric(
            projects.get("planned_duration_days"), errors="coerce").median()),
    }
    return {"dev": dev.to_dict(orient="index"),
            "type_categories": type_cats,
            "year_completion_median": year_median,
            "globals": globals_}


def save_reference(reference: dict) -> None:
    REFERENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(reference, REFERENCE_PATH)


def load_reference() -> Optional[dict]:
    if not REFERENCE_PATH.exists():
        return None
    ref = joblib.load(REFERENCE_PATH)
    # Reject stale reference files from older (area-based) model versions.
    if "dev" not in ref or "globals" not in ref:
        return None
    if "planned_duration_days" not in ref.get("globals", {}):
        return None
    if "year_completion_median" not in ref:
        return None
    return ref


def featurize_request(req: dict, reference: dict) -> pd.DataFrame:
    """Build the single-row feature frame the model expects from a raw request."""
    g = reference["globals"]
    dev = reference["dev"].get(req.get("developer_name"), {})

    no_units = float(req.get("no_of_units", 0) or 0)
    no_build = float(req.get("no_of_buildings", 0) or 0)
    no_villa = float(req.get("no_of_villas", 0) or 0)
    no_land = float(req.get("no_of_lands", 0) or 0)

    ptype = req.get("project_type")
    cats = reference["type_categories"]
    type_code = cats.index(ptype) if ptype in cats else -1

    duration = req.get("planned_duration_days")
    if duration is None or (isinstance(duration, float) and duration != duration):
        duration = g.get("planned_duration_days", 900.0)

    row = {
        "no_of_units": no_units,
        "no_of_buildings": no_build,
        "no_of_villas": no_villa,
        "no_of_lands": no_land,
        "total_assets": no_units + no_build + no_villa + no_land,
        "planned_duration_days": float(duration),
        "start_year": float(req.get("start_year", 2025)),
        "dev_n_projects": float(dev.get("dev_n_projects", g["dev_n_projects"])),
        "dev_total_units": float(dev.get("dev_total_units", g["dev_total_units"])),
        "dev_delivered_rate_loo": float(dev.get("dev_delivered_rate_loo", g["dev_delivered_rate_loo"])),
        "dev_avg_completion_loo": float(dev.get("dev_avg_completion_loo", g["dev_avg_completion_loo"])),
        "project_type_code": float(type_code),
    }
    return pd.DataFrame([row])[NUMERIC_FEATURES]


def cohort_context(pct: float, start_year, reference: dict) -> tuple[str, float]:
    """Cohort-aware risk band.

    The model predicts completion achieved to date, so raw percentages mean
    little without context: a 2025-start project at 4% is normal, while a
    2018-start project at 4% is stalled. This compares the prediction with the
    median completion of all projects that started the same year and returns
    ``(band, peer_median)``.
    """
    try:
        year = int(start_year)
    except (TypeError, ValueError):
        return risk_band(pct), float("nan")

    medians = reference.get("year_completion_median") or {}
    peer = medians.get(year)
    if peer is None and medians:
        if year > max(medians):
            peer = 0.0          # future cohort: nothing built yet
        elif year < min(medians):
            peer = 100.0        # historic cohort: peers long delivered
    if peer is None:
        return risk_band(pct), float("nan")

    if peer < 10.0:
        return "Early stage (cohort just started; risk not yet assessable)", peer
    ratio = pct / max(peer, 1.0)
    if ratio >= 0.9:
        return "In line with or ahead of its cohort (low delivery risk)", peer
    if ratio >= 0.65:
        return "Behind its cohort (moderate risk)", peer
    if ratio >= 0.35:
        return "Well behind its cohort (elevated risk)", peer
    return "Severely lagging its cohort (high risk)", peer


def risk_band(pct: float) -> str:
    if pct >= 80:
        return "Low risk (very likely to deliver)"
    if pct >= 55:
        return "Moderate risk"
    if pct >= 30:
        return "Elevated risk"
    return "High risk (delivery uncertain)"
