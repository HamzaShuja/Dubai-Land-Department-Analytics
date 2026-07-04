"""FastAPI service exposing the project-delivery model.

POST /predict accepts a project's attributes and returns the predicted eventual
completion percentage, a human-readable risk band, and a SHAP feature breakdown
explaining the prediction. The model and reference tables are loaded once at
startup.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# Make the src package importable when run as a script / in Docker.
SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from realestate.models import lgbm_model
from realestate.models.inference import (
    load_reference, featurize_request, risk_band,
)

app = FastAPI(
    title="Dubai Real Estate Analytics API",
    description="Project delivery-risk prediction with SHAP explainability.",
    version="1.0.0",
)

_STATE: dict = {"model": None, "reference": None}


def _ensure_loaded():
    if _STATE["model"] is None:
        _STATE["model"] = lgbm_model.load_model()
        _STATE["reference"] = load_reference()
    return _STATE["model"], _STATE["reference"]


class PredictRequest(BaseModel):
    developer_name: str = Field(..., examples=["اعمار العقارية (ش . م. ع)"])
    # Retained for backwards compatibility; the model is developer-centric and
    # no longer uses the area.
    area_name_en: Optional[str] = Field(None, examples=["Burj Khalifa"])
    no_of_units: int = Field(0, ge=0)
    no_of_buildings: int = Field(0, ge=0)
    no_of_villas: int = Field(0, ge=0)
    no_of_lands: int = Field(0, ge=0)
    project_type: Optional[str] = Field(None, examples=["عادي"])
    planned_duration_days: Optional[float] = Field(900, ge=0)
    start_year: int = Field(2025, ge=1990, le=2100)


class ShapContribution(BaseModel):
    feature: str
    value: float
    shap_value: float


class PredictResponse(BaseModel):
    predicted_completion_pct: float
    risk_band: str
    base_value: float
    top_factors: list[ShapContribution]
    model_metrics: dict


@app.get("/health")
def health():
    model, ref = _ensure_loaded()
    return {
        "status": "ok" if model is not None and ref is not None else "model_not_built",
        "model_loaded": model is not None,
        "reference_loaded": ref is not None,
    }


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    model, reference = _ensure_loaded()
    if model is None or reference is None:
        raise HTTPException(503, "Model artifacts not built. Run build_artifacts first.")

    X = featurize_request(req.model_dump(), reference)
    pred = float(np.clip(model.predict(X)[0], 0, 100))

    # SHAP explanation
    import shap
    explainer = shap.TreeExplainer(model.booster)
    shap_vals = explainer.shap_values(X[model.features])[0]
    base = float(explainer.expected_value)

    contribs = sorted(
        [ShapContribution(feature=f, value=float(X.iloc[0][f]), shap_value=float(sv))
         for f, sv in zip(model.features, shap_vals)],
        key=lambda c: abs(c.shap_value), reverse=True,
    )[:8]

    return PredictResponse(
        predicted_completion_pct=round(pred, 2),
        risk_band=risk_band(pred),
        base_value=round(base, 2),
        top_factors=contribs,
        model_metrics=model.metrics,
    )
