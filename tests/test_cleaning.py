"""Cleaning: dedup, types, derived columns."""
import pandas as pd
from realestate.cleaning import clean_transactions, clean_projects


def test_transactions_have_period(transactions):
    assert "period" in transactions.columns
    assert "period_label" in transactions.columns
    assert transactions["period"].is_monotonic_increasing or transactions["period"].notna().all()


def test_projects_derived_flags(projects):
    for col in ("is_ready", "is_offplan", "is_delivered", "total_assets",
                "planned_duration_days"):
        assert col in projects.columns
    # total_assets equals the sum of component counts.
    s = (projects["no_of_units"] + projects["no_of_buildings"]
         + projects["no_of_villas"] + projects["no_of_lands"])
    assert (projects["total_assets"] == s).all()


def test_dedup_idempotent(projects):
    again = clean_projects(projects)
    assert len(again) == len(projects)


def test_no_negative_durations(projects):
    durations = projects["planned_duration_days"].dropna()
    assert (durations >= 0).all()
