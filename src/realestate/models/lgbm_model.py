"""LightGBM project-delivery model with SHAP explainability and MLflow tracking.

Trains a gradient-boosted regressor that predicts a project's eventual
completion percentage. Every training run is logged to MLflow (params, metrics,
the serialised model, and a feature-importance artifact). A small grid of
configurations is compared and the best run (lowest validation MAE) is
registered as the production model.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from ..config import PROJECT_ROOT, get_settings
from ..logging_config import get_logger
from .features import build_features

log = get_logger(__name__)

MODEL_DIR = PROJECT_ROOT / "artifacts" / "models"
MODEL_PATH = MODEL_DIR / "delivery_lgbm.joblib"


@dataclass
class TrainedModel:
    booster: lgb.LGBMRegressor
    features: list[str]
    metrics: dict
    feature_importance: pd.DataFrame
    params: dict = field(default_factory=dict)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        preds = self.booster.predict(X[self.features])
        return np.clip(preds, 0, 100)


_PARAM_GRID = [
    {"n_estimators": 300, "learning_rate": 0.05, "num_leaves": 31, "max_depth": -1},
    {"n_estimators": 400, "learning_rate": 0.03, "num_leaves": 63, "max_depth": 8},
    {"n_estimators": 500, "learning_rate": 0.05, "num_leaves": 15, "max_depth": 6},
]


def _try_mlflow():
    try:
        import os
        import mlflow
        uri = get_settings().mlflow_tracking_uri
        if uri.startswith("sqlite:///"):
            raw = uri[len("sqlite:///"):]
            path = Path(raw)
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            path.parent.mkdir(parents=True, exist_ok=True)
            uri = "sqlite:///" + str(path)
        mlflow.set_tracking_uri(uri)
        mlflow.set_experiment("dubai-real-estate-delivery")
        return mlflow
    except Exception as exc:  # noqa: BLE001
        log.warning("MLflow unavailable (%s); training without tracking.", exc)
        return None


def train(projects: pd.DataFrame, seed: int = 42, register: bool = True) -> TrainedModel:
    df, feats, target = build_features(projects)
    X, y = df[feats], df[target]
    X_tr, X_val, y_tr, y_val = train_test_split(X, y, test_size=0.2, random_state=seed)

    mlflow = _try_mlflow()
    best: Optional[TrainedModel] = None
    best_mae = np.inf
    best_run_id = None

    for i, params in enumerate(_PARAM_GRID):
        model = lgb.LGBMRegressor(random_state=seed, n_jobs=-1, verbose=-1, **params)
        model.fit(X_tr, y_tr)
        pred = np.clip(model.predict(X_val), 0, 100)
        mae = mean_absolute_error(y_val, pred)
        r2 = r2_score(y_val, pred)
        metrics = {"val_mae": float(mae), "val_r2": float(r2),
                   "val_rmse": float(np.sqrt(((pred - y_val) ** 2).mean()))}
        imp = pd.DataFrame({"feature": feats, "importance": model.feature_importances_}) \
            .sort_values("importance", ascending=False).reset_index(drop=True)
        log.info("run %d: MAE=%.3f R2=%.3f params=%s", i, mae, r2, params)

        if mlflow is not None:
            with mlflow.start_run(run_name=f"lgbm_grid_{i}") as run:
                mlflow.log_params(params)
                mlflow.log_metrics(metrics)
                mlflow.log_dict(imp.to_dict(orient="records"), "feature_importance.json")
                try:
                    mlflow.lightgbm.log_model(model, name="model")
                except Exception:  # older mlflow API
                    mlflow.lightgbm.log_model(model, artifact_path="model")
                if mae < best_mae:
                    best_run_id = run.info.run_id

        if mae < best_mae:
            best_mae = mae
            best = TrainedModel(model, feats, metrics, imp, params)

    # Persist best model locally for the API / dashboard.
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": best.booster, "features": best.features,
                 "metrics": best.metrics, "params": best.params}, MODEL_PATH)
    (MODEL_DIR / "delivery_metrics.json").write_text(json.dumps(best.metrics, indent=2))

    # Persist developer/area reference tables for single-request inference.
    from .inference import build_reference, save_reference
    save_reference(build_reference(projects))
    log.info("Best model saved -> %s (MAE=%.3f)", MODEL_PATH, best_mae)

    if mlflow is not None and register and best_run_id:
        try:
            mlflow.register_model(f"runs:/{best_run_id}/model", "DubaiDeliveryModel")
            log.info("Registered best run %s as DubaiDeliveryModel", best_run_id)
        except Exception as exc:  # noqa: BLE001 — registry optional on file store
            log.warning("Model registry step skipped (%s)", exc)

    return best


def load_model() -> Optional[TrainedModel]:
    if not MODEL_PATH.exists():
        return None
    payload = joblib.load(MODEL_PATH)
    tm = TrainedModel(payload["model"], payload["features"], payload["metrics"],
                      pd.DataFrame(), payload.get("params", {}))
    return tm


def explain(model: TrainedModel, X: pd.DataFrame) -> pd.DataFrame:
    """Return per-feature SHAP contributions for the given rows."""
    import shap
    explainer = shap.TreeExplainer(model.booster)
    shap_values = explainer.shap_values(X[model.features])
    return pd.DataFrame(shap_values, columns=model.features, index=X.index)
