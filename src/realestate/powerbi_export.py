"""Power BI export: analytics-ready star schema from both datasets.

Produces the tables a professional Power BI model needs - clean English
values, pre-computed flags and reputation features, and proper dimension
tables - so the .pbix build is pure assembly:

    python -m realestate.powerbi_export     ->  powerbi/data/*.csv

Tables
------
FactTransactions  quarterly market activity (one row per quarter x property
                  type x transaction group, value + deal count in columns)
FactProjects      one row per registered project with delivery flags
DimDeveloper      developer track record + composite reliability score
DimArea           community roll-up with map coordinates
DimDate           quarter-grain date table covering the transaction history
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import PROJECT_ROOT, get_settings
from .logging_config import configure_logging, get_logger
from .ingestion import ingest
from .cleaning import clean_transactions, clean_projects
from .translation import developer_display, project_type_display
from .analysis.market import transaction_summary
from .analysis import market_intel as mi
from .geo import AREA_COORDS

log = get_logger(__name__)

EXPORT_DIR = PROJECT_ROOT / "powerbi" / "data"

_BANDS = [-0.1, 30, 70, 100.1]
_BAND_LABELS = ["<30% built", "30-70% built", ">70% built"]


def _quarter_start(year: int, quarter: int) -> pd.Timestamp:
    return pd.Timestamp(year=int(year), month=3 * (int(quarter) - 1) + 1, day=1)


def build_fact_transactions(tx: pd.DataFrame) -> pd.DataFrame:
    s = transaction_summary(tx)
    out = s.rename(columns={"count": "txn_count"}).copy()
    out["quarter_start"] = [
        _quarter_start(y, q) for y, q in zip(out["year"], out["quarter_number"])
    ]
    cols = ["quarter_start", "year", "quarter_number", "period_label",
            "property_type", "transaction_group", "value_aed", "txn_count"]
    return out[cols].sort_values(["quarter_start", "property_type", "transaction_group"])


def build_fact_projects(pr: pd.DataFrame, today=None) -> pd.DataFrame:
    today = pd.Timestamp(today) if today is not None else pd.Timestamp.today()
    df = pr.copy()
    end = pd.to_datetime(df["project_end_date"], errors="coerce")
    df["developer"] = df["developer_name"].map(developer_display)
    df["project_type_en"] = df["project_type"].map(project_type_display)
    df["is_overdue"] = df["is_offplan"] & end.notna() & (end < today)
    df["is_zombie"] = df["is_overdue"] & (df["percent_completed"] < 30.0)
    df["months_overdue"] = np.where(
        df["is_overdue"], ((today - end).dt.days / 30.44).round(1), np.nan)
    df["end_year"] = end.dt.year
    df["progress_band"] = pd.cut(df["percent_completed"], _BANDS, labels=_BAND_LABELS)
    cohort = (df.dropna(subset=["start_year"])
                .groupby("start_year")["percent_completed"].median()
                .rename("cohort_median_completion"))
    df = df.merge(cohort, left_on="start_year", right_index=True, how="left")
    df["vs_cohort_pts"] = df["percent_completed"] - df["cohort_median_completion"]
    cols = ["project_id", "master_project_en", "area_name_en", "developer",
            "project_status", "project_type_en", "percent_completed",
            "no_of_units", "no_of_buildings", "no_of_villas", "no_of_lands",
            "total_assets", "project_start_date", "project_end_date",
            "start_year", "end_year", "planned_duration_days",
            "is_ready", "is_offplan", "is_delivered", "is_overdue", "is_zombie",
            "months_overdue", "progress_band", "cohort_median_completion",
            "vs_cohort_pts"]
    cols = [c for c in cols if c in df.columns]
    return df[cols]


def build_dim_developer(pr: pd.DataFrame, today=None) -> pd.DataFrame:
    rel = mi.developer_reliability(pr, min_projects=1, today=today)
    rel["developer"] = rel["developer_name"].map(developer_display)
    # Score only developers with a meaningful track record (10+ projects).
    rel.loc[rel["n_projects"] < 10, "reliability_score"] = np.nan
    rel["reliability_tier"] = pd.cut(
        rel["reliability_score"], [-0.1, 40, 60, 80, 100.1],
        labels=["High risk", "Below average", "Dependable", "Excellent"])
    cols = ["developer", "n_projects", "total_units", "delivered_rate",
            "avg_completion", "overdue_projects", "overdue_units",
            "overdue_share", "reliability_score", "reliability_tier"]
    return rel[cols].sort_values("reliability_score", ascending=False)


def build_dim_area(pr: pd.DataFrame, today=None) -> pd.DataFrame:
    today = pd.Timestamp(today) if today is not None else pd.Timestamp.today()
    df = pr.copy()
    end = pd.to_datetime(df["project_end_date"], errors="coerce")
    df["is_overdue"] = df["is_offplan"] & end.notna() & (end < today)
    df["overdue_units_row"] = np.where(df["is_overdue"], df["no_of_units"], 0)
    df["offplan_units_row"] = np.where(df["is_offplan"], df["no_of_units"], 0)
    g = (df.groupby("area_name_en", as_index=False)
           .agg(n_projects=("project_id", "count"),
                total_units=("no_of_units", "sum"),
                offplan_units=("offplan_units_row", "sum"),
                overdue_units=("overdue_units_row", "sum"),
                avg_completion=("percent_completed", "mean"),
                delivery_rate=("is_delivered", "mean")))
    g["delivery_rate"] *= 100.0
    g["latitude"] = g["area_name_en"].map(lambda a: (AREA_COORDS.get(a) or (np.nan, np.nan))[0])
    g["longitude"] = g["area_name_en"].map(lambda a: (AREA_COORDS.get(a) or (np.nan, np.nan))[1])
    return g.round(2)


def build_dim_date(tx: pd.DataFrame) -> pd.DataFrame:
    years = range(int(tx["year"].min()), int(tx["year"].max()) + 1)
    rows = [{"quarter_start": _quarter_start(y, q), "year": y, "quarter_number": q,
             "period_label": f"{y}Q{q}"} for y in years for q in (1, 2, 3, 4)]
    d = pd.DataFrame(rows)
    d["year_quarter_sort"] = d["year"] * 10 + d["quarter_number"]
    return d


def export(today=None) -> dict[str, Path]:
    settings = get_settings()
    tx = clean_transactions(ingest(settings).transactions)
    pr = clean_projects(ingest(settings).projects)

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    tables = {
        "FactTransactions": build_fact_transactions(tx),
        "FactProjects": build_fact_projects(pr, today),
        "DimDeveloper": build_dim_developer(pr, today),
        "DimArea": build_dim_area(pr, today),
        "DimDate": build_dim_date(tx),
    }
    paths = {}
    for name, df in tables.items():
        p = EXPORT_DIR / f"{name}.csv"
        df.to_csv(p, index=False, encoding="utf-8-sig")   # BOM helps Power BI
        paths[name] = p
        log.info("Exported %s: %d rows -> %s", name, len(df), p)
    return paths


def main() -> None:
    configure_logging(get_settings().log_level)
    paths = export()
    for name, p in paths.items():
        print(f"{name}: {p}")


if __name__ == "__main__":
    main()
