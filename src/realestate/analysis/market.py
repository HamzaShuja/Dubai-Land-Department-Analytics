"""Market analysis on the aggregated quarterly transactions dataset.

Provides the building blocks for the dashboard's Market Overview page:

* ``transaction_summary``   – tidy wide table (Value & Number per quarter/type).
* ``average_value_per_txn`` – derived mean AED per transaction over time.
* ``price_index``           – the **custom Dubai Real Estate Price Index**: a
  rebased rolling index (base period = 100) per property type, tracking how the
  average sale value per transaction moves over time.
* ``volume_trends`` / ``value_trends`` – total counts / AED by period.
* ``seasonal_profile``      – average activity by calendar quarter, with a simple
  seasonality strength metric.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def transaction_summary(tx: pd.DataFrame) -> pd.DataFrame:
    """Pivot the long transactions table to one row per
    period/property_type/transaction_group with Value & Number columns."""
    wide = (
        tx.pivot_table(
            index=["year", "quarter_number", "period", "period_label",
                   "property_type", "transaction_group"],
            columns="measure", values="amount", aggfunc="sum",
        )
        .reset_index()
        .rename(columns={"Value": "value_aed", "Number": "count"})
    )
    wide.columns.name = None
    for c in ("value_aed", "count"):
        if c not in wide.columns:
            wide[c] = np.nan
    wide["avg_value_per_txn"] = wide["value_aed"] / wide["count"].replace(0, np.nan)
    return wide.sort_values(["period", "property_type", "transaction_group"]).reset_index(drop=True)


def average_value_per_txn(tx: pd.DataFrame, group: str = "Sales") -> pd.DataFrame:
    s = transaction_summary(tx)
    s = s[s["transaction_group"] == group]
    return s.pivot_table(
        index=["period", "period_label"], columns="property_type",
        values="avg_value_per_txn",
    ).reset_index()


def price_index(tx: pd.DataFrame, group: str = "Sales", smooth: int = 1) -> pd.DataFrame:
    """Custom price index: average value per transaction per property type,
    rebased so the first available period = 100. Optionally smoothed with a
    trailing rolling mean of ``smooth`` quarters."""
    s = transaction_summary(tx)
    s = s[s["transaction_group"] == group].copy()
    out = []
    for ptype, g in s.groupby("property_type"):
        g = g.sort_values("period")
        series = g["avg_value_per_txn"].astype(float)
        if smooth > 1:
            series = series.rolling(smooth, min_periods=1).mean()
        base = series.dropna().iloc[0] if series.notna().any() else np.nan
        idx = series / base * 100.0 if base and not np.isnan(base) else series * np.nan
        out.append(pd.DataFrame({
            "period": g["period"].values,
            "period_label": g["period_label"].values,
            "property_type": ptype,
            "index_value": idx.values,
        }))
    return pd.concat(out, ignore_index=True).sort_values(["property_type", "period"])


def volume_trends(tx: pd.DataFrame, group: str = "Sales") -> pd.DataFrame:
    s = transaction_summary(tx)
    s = s[s["transaction_group"] == group]
    return (
        s.groupby(["period", "period_label"], as_index=False)[["count", "value_aed"]]
        .sum()
        .sort_values("period")
    )


def seasonal_profile(tx: pd.DataFrame, group: str = "Sales") -> pd.DataFrame:
    """Average transaction count by calendar quarter (1–4) with a seasonality
    strength score = std across quarters / overall mean."""
    s = transaction_summary(tx)
    s = s[s["transaction_group"] == group]
    by_q = s.groupby("quarter_number", as_index=False)["count"].mean()
    overall = by_q["count"].mean()
    by_q["seasonality_strength"] = by_q["count"].std() / overall if overall else np.nan
    by_q["pct_of_avg"] = by_q["count"] / overall * 100.0
    return by_q
