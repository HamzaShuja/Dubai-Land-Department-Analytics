"""Data cleaning: deduplication, type casting, and derived columns.

Runs after validation and before the database load. Cleaning is deterministic
and logged so each run reports how many duplicates were removed and which
derived fields were added.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .logging_config import get_logger

log = get_logger(__name__)

_READY = {"Finished"}
_OFFPLAN = {"Active", "Not Started", "Pending", "Conditional Activating"}


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.drop_duplicates(
        subset=["year", "quarter_number", "property_type", "transaction_group", "measure"]
    )
    log.info("transactions: dropped %d duplicate rows", before - len(df))

    df["year"] = df["year"].astype(int)
    df["quarter_number"] = df["quarter_number"].astype(int)
    df["amount"] = df["amount"].astype(float)

    # Ordered period key for time-series work (e.g. 2024Q3 -> 2024.50).
    df["period"] = df["year"] + (df["quarter_number"] - 1) / 4.0
    df["period_label"] = df["year"].astype(str) + "Q" + df["quarter_number"].astype(str)
    df = df.sort_values(["period", "property_type", "transaction_group", "measure"])
    return df.reset_index(drop=True)


def clean_projects(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.drop_duplicates(subset=["project_id"])
    log.info("projects: dropped %d duplicate rows", before - len(df))

    for col in ("project_start_date", "project_end_date"):
        df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in ("no_of_units", "no_of_buildings", "no_of_villas", "no_of_lands"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["percent_completed"] = pd.to_numeric(df["percent_completed"], errors="coerce").fillna(0.0)

    # Nullable integer IDs (preserve NULLs instead of forcing float NaN).
    for col in ("project_id", "area_id", "developer_id"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # Derived analytical columns.
    df["planned_duration_days"] = (
        (df["project_end_date"] - df["project_start_date"]).dt.days
    )
    df.loc[df["planned_duration_days"] < 0, "planned_duration_days"] = np.nan

    df["is_ready"] = df["project_status"].isin(_READY)
    df["is_offplan"] = df["project_status"].isin(_OFFPLAN)
    df["is_delivered"] = df["percent_completed"] >= 100.0
    df["total_assets"] = (
        df["no_of_units"] + df["no_of_buildings"] + df["no_of_villas"] + df["no_of_lands"]
    )
    df["start_year"] = df["project_start_date"].dt.year

    log.info("projects: cleaned %d rows (%d ready, %d off-plan)",
             len(df), int(df["is_ready"].sum()), int(df["is_offplan"].sum()))
    return df.reset_index(drop=True)
