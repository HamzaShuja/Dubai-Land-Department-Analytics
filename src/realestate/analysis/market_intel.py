"""High-impact market-intelligence metrics.

These are the decision-relevant figures a professional real-estate dashboard
leads with: market momentum (with correct, label-based year-over-year that
tolerates the missing 2024 data), the forward supply pipeline by expected
completion year, delivery-risk exposure, and market concentration.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

from .market import transaction_summary


# --------------------------------------------------------------------------- #
# Data coverage
# --------------------------------------------------------------------------- #
def coverage(tx: pd.DataFrame) -> dict:
    years = sorted(tx["year"].unique().tolist())
    full = set(range(min(years), max(years) + 1))
    missing = sorted(full - set(years))
    return {"years": years, "missing": missing,
            "label": f"{min(years)}–{max(years)}",
            "note": ("2024 not published in this Dubai Pulse dataset"
                     if 2024 in missing else "")}


# --------------------------------------------------------------------------- #
# Market momentum
# --------------------------------------------------------------------------- #
@dataclass
class Momentum:
    period_label: str
    value_aed: float
    count: float
    all_time_high: bool
    yoy_pct: float | None          # same quarter, previous year (None if absent)
    yoy_label: str | None
    last_comp_pct: float           # vs most recent earlier quarter available
    last_comp_label: str
    cagr_pct: float                # annualised, first→last
    first_label: str
    first_value: float

    def to_dict(self):
        return asdict(self)


def market_momentum(tx: pd.DataFrame, group: str = "Sales") -> Momentum:
    s = transaction_summary(tx)
    s = s[s["transaction_group"] == group]
    byq = (s.groupby(["period_label", "period", "year", "quarter_number"], as_index=False)
             .agg(value=("value_aed", "sum"), count=("count", "sum"))
             .sort_values("period").reset_index(drop=True))
    latest = byq.iloc[-1]
    first = byq.iloc[0]

    # True YoY: same quarter, previous calendar year.
    prev = byq[(byq["year"] == latest["year"] - 1)
               & (byq["quarter_number"] == latest["quarter_number"])]
    yoy_pct = yoy_label = None
    if len(prev):
        yoy_pct = (latest["value"] / prev.iloc[0]["value"] - 1) * 100
        yoy_label = prev.iloc[0]["period_label"]

    # Growth vs the most recent earlier quarter that exists (honest fallback).
    prior = byq.iloc[-2]
    last_comp_pct = (latest["value"] / prior["value"] - 1) * 100

    years_elapsed = max(latest["period"] - first["period"], 1e-9)
    cagr_pct = ((latest["value"] / first["value"]) ** (1 / years_elapsed) - 1) * 100

    return Momentum(
        period_label=latest["period_label"], value_aed=float(latest["value"]),
        count=float(latest["count"]),
        all_time_high=bool(latest["value"] >= byq["value"].max()),
        yoy_pct=yoy_pct, yoy_label=yoy_label,
        last_comp_pct=float(last_comp_pct), last_comp_label=prior["period_label"],
        cagr_pct=float(cagr_pct),
        first_label=first["period_label"], first_value=float(first["value"]),
    )


# --------------------------------------------------------------------------- #
# Supply pipeline & delivery-risk exposure
# --------------------------------------------------------------------------- #
def supply_pipeline(projects: pd.DataFrame) -> pd.DataFrame:
    """Off-plan units by expected completion (project_end_date) year."""
    df = projects[projects["is_offplan"]].copy()
    df["end_year"] = pd.to_datetime(df["project_end_date"], errors="coerce").dt.year
    pipe = (df.dropna(subset=["end_year"])
              .groupby("end_year", as_index=False)
              .agg(projects=("project_id", "count"), units=("no_of_units", "sum")))
    pipe["end_year"] = pipe["end_year"].astype(int)
    pipe = pipe[pipe["end_year"] >= 2024].sort_values("end_year")
    pipe["cumulative_units"] = pipe["units"].cumsum()
    return pipe.reset_index(drop=True)


def delivery_risk_exposure(projects: pd.DataFrame, threshold: float = 30.0) -> dict:
    offplan = projects[projects["is_offplan"]]
    pipeline_units = int(offplan["no_of_units"].sum())
    at_risk = offplan[offplan["percent_completed"] < threshold]
    at_risk_units = int(at_risk["no_of_units"].sum())
    return {
        "pipeline_units": pipeline_units,
        "at_risk_units": at_risk_units,
        "at_risk_projects": int(len(at_risk)),
        "at_risk_share": (at_risk_units / pipeline_units * 100) if pipeline_units else 0.0,
        "threshold": threshold,
    }


# --------------------------------------------------------------------------- #
# Market concentration
# --------------------------------------------------------------------------- #
def _concentration(projects: pd.DataFrame, key: str, n: int) -> dict:
    g = projects.groupby(key)["no_of_units"].sum().sort_values(ascending=False)
    total = g.sum()
    shares = (g / total * 100) if total else g
    hhi = float(((g / total) ** 2).sum() * 10000) if total else 0.0  # 0–10000
    top = shares.head(n)
    return {
        "top_n_share": float(top.sum()),
        "n": n,
        "hhi": hhi,
        "top": [(name, int(g[name]), float(shares[name])) for name in top.index],
        "total_units": int(total),
    }


def developer_concentration(projects: pd.DataFrame, n: int = 5) -> dict:
    return _concentration(projects, "developer_name", n)


def area_concentration(projects: pd.DataFrame, n: int = 5) -> dict:
    return _concentration(projects, "area_name_en", n)


def at_risk_by_area(projects: pd.DataFrame, threshold: float = 30.0, n: int = 10) -> pd.DataFrame:
    off = projects[projects["is_offplan"]].copy()
    off["at_risk_units"] = np.where(off["percent_completed"] < threshold, off["no_of_units"], 0)
    g = (off.groupby("area_name_en", as_index=False)
            .agg(pipeline_units=("no_of_units", "sum"),
                 at_risk_units=("at_risk_units", "sum")))
    g["at_risk_share"] = g["at_risk_units"] / g["pipeline_units"].replace(0, np.nan) * 100
    return g.sort_values("at_risk_units", ascending=False).head(n).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Credit profile: how leveraged is the market?
# --------------------------------------------------------------------------- #
def credit_profile(tx: pd.DataFrame) -> dict:
    """Mortgage-to-sales value ratio per quarter.

    A falling ratio means the market is increasingly cash-driven (less
    financing risk, more equity buyers); a spike signals leverage building up.
    """
    s = transaction_summary(tx)
    v = (s.pivot_table(index=["period", "period_label"], columns="transaction_group",
                       values="value_aed", aggfunc="sum").reset_index()
         .sort_values("period"))
    v["mortgage_to_sales"] = v.get("Mortgages", np.nan) / v.get("Sales", np.nan)
    series = v[["period", "period_label", "Sales", "Mortgages", "mortgage_to_sales"]].dropna()
    early = float(series["mortgage_to_sales"].head(4).mean())
    recent = float(series["mortgage_to_sales"].tail(4).mean())
    return {
        "series": series.reset_index(drop=True),
        "early_avg": early,
        "recent_avg": recent,
        "latest": float(series["mortgage_to_sales"].iloc[-1]),
        "latest_label": str(series["period_label"].iloc[-1]),
    }


# --------------------------------------------------------------------------- #
# Average ticket (value per transaction) by property type
# --------------------------------------------------------------------------- #
def ticket_trends(tx: pd.DataFrame, group: str = "Sales") -> dict:
    """Average sale value per transaction, by property type, over time.

    This is the closest thing to a price signal in the aggregated dataset:
    it shows *where* value growth is happening (e.g. villas repricing faster
    than apartments)."""
    s = transaction_summary(tx)
    s = s[s["transaction_group"] == group].copy()
    series = s[["period", "period_label", "property_type", "avg_value_per_txn"]].dropna()
    latest = series[series["period"] == series["period"].max()]
    summary = []
    for ptype, grp in series.groupby("property_type"):
        grp = grp.sort_values("period")
        if len(grp) < 5:
            continue
        now = float(grp["avg_value_per_txn"].iloc[-1])
        yr_ago = float(grp["avg_value_per_txn"].iloc[-5])  # 4 quarters back
        summary.append({"property_type": ptype, "latest": now,
                        "chg_4q_pct": (now / yr_ago - 1) * 100 if yr_ago else np.nan})
    return {"series": series.reset_index(drop=True),
            "summary": pd.DataFrame(summary),
            "latest_label": str(latest["period_label"].iloc[0]) if len(latest) else ""}


def sales_mix(tx: pd.DataFrame) -> pd.DataFrame:
    """Share of quarterly sales value by property type (mix shift over time)."""
    s = transaction_summary(tx)
    s = s[s["transaction_group"] == "Sales"]
    piv = s.pivot_table(index=["period", "period_label"], columns="property_type",
                        values="value_aed", aggfunc="sum")
    mix = piv.div(piv.sum(axis=1), axis=0) * 100
    return mix.reset_index().sort_values("period").reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Overdue / zombie watchlist — the actionable delivery-risk list
# --------------------------------------------------------------------------- #
def overdue_watchlist(projects: pd.DataFrame, today=None,
                      zombie_threshold: float = 30.0) -> dict:
    """Off-plan projects already past their planned end date.

    ``is_zombie`` marks the worst cases: overdue AND less than
    ``zombie_threshold``% built — projects that realistically will not deliver
    without re-planning. Returns the watchlist plus headline totals.
    """
    today = pd.Timestamp(today) if today is not None else pd.Timestamp.today()
    off = projects[projects["is_offplan"]].copy()
    end = pd.to_datetime(off["project_end_date"], errors="coerce")
    over = off[end.notna() & (end < today)].copy()
    over["months_overdue"] = ((today - pd.to_datetime(over["project_end_date"])).dt.days / 30.44).round(1)
    over["is_zombie"] = over["percent_completed"] < zombie_threshold
    cols = ["project_id", "master_project_en", "area_name_en", "developer_name",
            "project_status", "percent_completed", "no_of_units",
            "project_end_date", "months_overdue", "is_zombie"]
    cols = [c for c in cols if c in over.columns]
    wl = over[cols].sort_values(["is_zombie", "no_of_units"], ascending=[False, False])
    return {
        "watchlist": wl.reset_index(drop=True),
        "n_overdue": int(len(over)),
        "overdue_units": int(over["no_of_units"].sum()),
        "n_zombie": int(over["is_zombie"].sum()),
        "zombie_units": int(over.loc[over["is_zombie"], "no_of_units"].sum()),
        "threshold": zombie_threshold,
    }


# --------------------------------------------------------------------------- #
# Developer reliability scores
# --------------------------------------------------------------------------- #
def developer_reliability(projects: pd.DataFrame, min_projects: int = 10,
                          today=None) -> pd.DataFrame:
    """Composite delivery-reliability score per developer (0–100).

    Blends delivered rate (40%), average completion (30%) and the share of the
    developer's off-plan portfolio that is already overdue (30%, inverted).
    Only developers with at least ``min_projects`` tracked projects are scored,
    so single-project SPVs don't distort the ranking.
    """
    today = pd.Timestamp(today) if today is not None else pd.Timestamp.today()
    df = projects.copy()
    end = pd.to_datetime(df["project_end_date"], errors="coerce")
    df["is_overdue"] = df["is_offplan"] & end.notna() & (end < today)

    g = df.groupby("developer_name").agg(
        n_projects=("project_id", "count"),
        total_units=("no_of_units", "sum"),
        delivered_rate=("is_delivered", "mean"),
        avg_completion=("percent_completed", "mean"),
        overdue_projects=("is_overdue", "sum"),
        overdue_units=("no_of_units", lambda s: int(s[df.loc[s.index, "is_overdue"]].sum())),
    )
    g["overdue_share"] = g["overdue_projects"] / g["n_projects"]
    g["delivered_rate"] *= 100
    g = g[g["n_projects"] >= min_projects].copy()
    g["reliability_score"] = (0.4 * g["delivered_rate"]
                              + 0.3 * g["avg_completion"]
                              + 0.3 * (100 - g["overdue_share"] * 100))
    return (g.sort_values("reliability_score", ascending=False)
             .reset_index().round(1))


# --------------------------------------------------------------------------- #
# Credibility-weighted supply pipeline
# --------------------------------------------------------------------------- #
def realistic_pipeline(projects: pd.DataFrame, first_year: int = 2024) -> pd.DataFrame:
    """Stated pipeline by completion year, split by build progress.

    Units due soon in projects that are barely built will not arrive on
    schedule; splitting the stated pipeline into progress bands shows how much
    of it is credible."""
    off = projects[projects["is_offplan"]].copy()
    off["end_year"] = pd.to_datetime(off["project_end_date"], errors="coerce").dt.year
    off = off.dropna(subset=["end_year"])
    off["end_year"] = off["end_year"].astype(int)
    off = off[off["end_year"] >= first_year]
    bands = pd.cut(off["percent_completed"], [-0.1, 30, 70, 100.1],
                   labels=["<30% built", "30–70% built", ">70% built"])
    out = (off.groupby(["end_year", bands], observed=True)["no_of_units"]
           .sum().reset_index()
           .rename(columns={"percent_completed": "progress_band", "no_of_units": "units"}))
    return out
