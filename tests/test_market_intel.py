"""High-impact market-intelligence metrics."""
from realestate.analysis import market_intel as mi


def test_coverage_flags_missing_2024(transactions):
    cov = mi.coverage(transactions)
    assert 2024 in cov["missing"]
    assert cov["note"]


def test_momentum_yoy_none_when_prior_year_absent(transactions):
    m = mi.market_momentum(transactions)
    # 2024 is missing, so a true YoY for a 2025 quarter must be None (not fabricated).
    assert m.yoy_pct is None
    assert m.all_time_high in (True, False)
    assert m.cagr_pct > 0


def test_supply_pipeline_sorted_and_cumulative(projects):
    pipe = mi.supply_pipeline(projects)
    assert (pipe["end_year"].is_monotonic_increasing)
    assert (pipe["cumulative_units"].diff().dropna() >= 0).all()
    assert pipe["units"].sum() > 0


def test_delivery_risk_exposure_bounds(projects):
    r = mi.delivery_risk_exposure(projects)
    assert 0 <= r["at_risk_share"] <= 100
    assert r["at_risk_units"] <= r["pipeline_units"]


def test_concentration_shares(projects):
    d = mi.developer_concentration(projects, 5)
    assert 0 < d["top_n_share"] <= 100
    assert 0 <= d["hhi"] <= 10000
    assert len(d["top"]) == 5


def test_credit_profile(transactions):
    from realestate.analysis import market_intel as mi
    cp = mi.credit_profile(transactions)
    assert 0 < cp["latest"] < 5
    assert cp["early_avg"] > cp["recent_avg"]  # documented deleveraging trend
    assert len(cp["series"]) > 20


def test_ticket_trends_and_mix(transactions):
    from realestate.analysis import market_intel as mi
    tt = mi.ticket_trends(transactions)
    assert not tt["summary"].empty
    assert (tt["summary"]["latest"] > 0).all()
    mix = mi.sales_mix(transactions)
    shares = mix.drop(columns=["period", "period_label"]).sum(axis=1)
    assert ((shares - 100).abs() < 1e-6).all()  # shares sum to 100%


def test_overdue_watchlist(projects):
    from realestate.analysis import market_intel as mi
    wl = mi.overdue_watchlist(projects)
    assert wl["n_overdue"] > 0
    assert wl["n_zombie"] <= wl["n_overdue"]
    assert wl["zombie_units"] <= wl["overdue_units"]
    w = wl["watchlist"]
    assert (w.loc[w["is_zombie"], "percent_completed"] < wl["threshold"]).all()
    assert (w["months_overdue"] > 0).all()


def test_developer_reliability(projects):
    from realestate.analysis import market_intel as mi
    rel = mi.developer_reliability(projects, min_projects=10)
    assert (rel["n_projects"] >= 10).all()
    assert rel["reliability_score"].between(0, 100).all()
    assert rel["reliability_score"].is_monotonic_decreasing


def test_realistic_pipeline(projects):
    from realestate.analysis import market_intel as mi
    rp = mi.realistic_pipeline(projects)
    off = projects[projects["is_offplan"]]
    import pandas as pd
    end_years = pd.to_datetime(off["project_end_date"], errors="coerce").dt.year
    expected = off[end_years >= 2024]["no_of_units"].sum()
    assert rp["units"].sum() == expected  # bands partition the stated pipeline
