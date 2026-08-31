"""Power BI star-schema export."""
import re

from realestate.powerbi_export import (
    build_fact_transactions, build_fact_projects,
    build_dim_developer, build_dim_area, build_dim_date,
)

_AR = re.compile(r"[؀-ۿ]")


def test_fact_projects_clean_and_flagged(projects):
    fp = build_fact_projects(projects, today="2026-08-04")
    assert fp["project_id"].is_unique
    assert not fp["developer"].astype(str).str.contains(_AR).any()
    assert fp["is_zombie"].sum() <= fp["is_overdue"].sum()
    assert (fp.loc[fp["is_overdue"], "months_overdue"] >= 0).all()
    assert fp["progress_band"].notna().all()


def test_dim_developer_scoring(projects):
    dd = build_dim_developer(projects, today="2026-08-04")
    assert dd["developer"].is_unique
    scored = dd[dd["reliability_score"].notna()]
    assert (scored["n_projects"] >= 10).all()
    assert scored["reliability_score"].between(0, 100).all()


def test_transactions_and_dates_join(transactions):
    ft = build_fact_transactions(transactions)
    dd = build_dim_date(transactions)
    assert ft["quarter_start"].isin(dd["quarter_start"]).all()
    assert not ft[["quarter_start", "property_type", "transaction_group"]].duplicated().any()


def test_dim_area_totals_match(projects):
    da = build_dim_area(projects, today="2026-08-04")
    assert da["total_units"].sum() == projects["no_of_units"].sum()
    assert da["latitude"].notna().sum() > 20
