"""Analysis: price index, seasonality, developer reputation, stats, anomalies."""
import numpy as np

from realestate.analysis import market, developers, anomaly, stats_tests
from realestate.analysis.projects_analysis import area_summary, offplan_vs_ready


def test_price_index_rebased_to_100(transactions):
    idx = market.price_index(transactions, "Sales")
    firsts = (idx.dropna(subset=["index_value"])
              .sort_values("period").groupby("property_type")["index_value"].first())
    assert np.allclose(firsts.values, 100.0)


def test_seasonal_profile_four_quarters(transactions):
    s = market.seasonal_profile(transactions, "Sales")
    assert set(s["quarter_number"]) == {1, 2, 3, 4}


def test_developer_reputation_bounds(projects):
    rep = developers.developer_reputation(projects, min_projects=3)
    assert (rep["reputation_score"] >= 0).all()
    assert rep["delivered_rate"].between(0, 100).all()
    assert rep["reputation_score"].is_monotonic_decreasing


def test_hypothesis_test_outputs(transactions, projects):
    res = stats_tests.compare_property_type_prices(transactions, "Villa", "Units")
    assert 0 <= res.t_pvalue <= 1
    assert 0 <= res.mw_pvalue <= 1
    res2 = stats_tests.compare_offplan_vs_ready_completion(projects)
    assert res2.mean_b > res2.mean_a  # ready projects more complete


def test_anomaly_detection_flags_some(transactions, projects):
    ta = anomaly.detect_transaction_anomalies(transactions)
    assert ta["is_anomaly"].sum() >= 1
    pa = anomaly.detect_project_anomalies(projects)
    assert "anomaly_score" in pa.columns


def test_area_and_offplan_summaries(projects):
    a = area_summary(projects)
    assert a["n_projects"].sum() == len(projects)
    ovr = offplan_vs_ready(projects)
    assert set(ovr["segment"]) == {"Off-plan", "Ready"}
