"""ML pipeline: features, LightGBM, segmentation, forecasting, inference."""
import numpy as np

from realestate.models.features import build_features, NUMERIC_FEATURES
from realestate.models.segmentation import segment_areas
from realestate.models.inference import (build_reference, featurize_request,
                                          risk_band, cohort_context)


def test_features_no_nan(projects):
    df, feats, target = build_features(projects)
    assert feats == NUMERIC_FEATURES
    assert not df[feats].isna().any().any()
    assert target == "percent_completed"


def test_model_trains_and_is_reasonable(trained_model):
    assert trained_model.metrics["val_r2"] > 0.5
    assert trained_model.metrics["val_mae"] < 20


def test_predictions_in_range(trained_model, projects):
    df, feats, _ = build_features(projects)
    preds = trained_model.predict(df.head(50))
    assert preds.min() >= 0 and preds.max() <= 100


def test_segmentation_tiers_ordered(projects):
    seg = segment_areas(projects, k=4)
    tier_means = (seg.groupby("tier_rank")["delivery_rate"].mean()
                  .sort_index())
    # Tier 1 should have the highest mean delivery rate.
    assert tier_means.idxmin() == tier_means.index.max()
    assert tier_means.iloc[0] >= tier_means.iloc[-1]


def test_reference_and_featurize(projects):
    ref = build_reference(projects)
    assert ref["dev"] and ref["globals"]
    # Unknown developer falls back to global medians; no area input is needed.
    X = featurize_request(
        {"developer_name": "unknown",
         "no_of_units": 100, "project_type": None,
         "planned_duration_days": 900, "start_year": 2024},
        ref)
    assert list(X.columns) == NUMERIC_FEATURES
    assert not X.isna().any().any()


def test_featurize_known_developer_uses_track_record(projects):
    ref = build_reference(projects)
    dev = max(ref["dev"], key=lambda d: ref["dev"][d]["dev_n_projects"])
    X = featurize_request({"developer_name": dev, "no_of_units": 100}, ref)
    assert float(X["dev_n_projects"].iloc[0]) == ref["dev"][dev]["dev_n_projects"]
    # Missing duration falls back to the global median duration, not a count.
    Xd = featurize_request({"developer_name": dev}, ref)
    assert float(Xd["planned_duration_days"].iloc[0]) == ref["globals"]["planned_duration_days"]


def test_risk_band_monotonic():
    assert "Low" in risk_band(95)
    assert "High" in risk_band(10)


def test_prophet_forecast(transactions):
    from realestate.models.forecast import forecast_property_type
    fc = forecast_property_type(transactions, "Units", periods=4)
    assert fc["is_forecast"].sum() == 4
    fut = fc[fc["is_forecast"]]
    assert (fut["yhat_upper"] >= fut["yhat_lower"]).all()


def test_cohort_context_bands(projects):
    from realestate.models.inference import build_reference
    ref = build_reference(projects)
    band, peer = cohort_context(2.0, 2026, ref)
    assert "Early stage" in band          # 2026 cohort barely started
    band, peer = cohort_context(95.0, 2018, ref)
    assert "low delivery risk" in band and peer >= 90
    band, _ = cohort_context(10.0, 2018, ref)
    assert "high risk" in band
    band, peer = cohort_context(50.0, None, ref)
    assert peer != peer                   # NaN -> falls back to static band
