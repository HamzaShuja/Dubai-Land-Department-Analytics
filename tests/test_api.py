"""FastAPI /predict endpoint (exercised via the route functions)."""
import pytest

import api.main as apimod


@pytest.fixture(scope="module", autouse=True)
def _artifacts(projects):
    # Ensure a model + reference exist for the API to load.
    from realestate.models import lgbm_model
    lgbm_model.train(projects, register=False)
    apimod._STATE["model"] = None  # force reload
    apimod._STATE["reference"] = None


def test_health_ok():
    h = apimod.health()
    assert h["model_loaded"] and h["reference_loaded"]


def test_predict_returns_explanation():
    req = apimod.PredictRequest(
        developer_name="اعمار العقارية (ش . م. ع)", area_name_en="Burj Khalifa",
        no_of_units=500, no_of_buildings=1, project_type="عادي",
        planned_duration_days=900, start_year=2025)
    resp = apimod.predict(req)
    assert 0 <= resp.predicted_completion_pct <= 100
    assert resp.risk_band
    assert len(resp.top_factors) > 0
    # SHAP contributions are floats and the top factor is the most influential.
    abs_vals = [abs(c.shap_value) for c in resp.top_factors]
    assert abs_vals == sorted(abs_vals, reverse=True)
