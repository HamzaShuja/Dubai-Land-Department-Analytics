"""Prophet 12-month (4-quarter) price/activity forecasting.

Fits one Prophet model per property type on the quarterly average sale value per
transaction and projects four quarters ahead with 80% confidence intervals.
Prophet is imported lazily so the rest of the platform runs even where Prophet's
compiled backend is unavailable.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..analysis.market import transaction_summary
from ..logging_config import get_logger

log = get_logger(__name__)


def _quarter_to_date(year: int, q: int) -> pd.Timestamp:
    month = (q - 1) * 3 + 1
    return pd.Timestamp(year=int(year), month=month, day=1)


def build_series(tx: pd.DataFrame, property_type: str, group: str = "Sales") -> pd.DataFrame:
    s = transaction_summary(tx)
    s = s[(s["transaction_group"] == group) & (s["property_type"] == property_type)].copy()
    s["ds"] = [_quarter_to_date(y, q) for y, q in zip(s["year"], s["quarter_number"])]
    s["y"] = s["avg_value_per_txn"]
    return s[["ds", "y"]].dropna().sort_values("ds").reset_index(drop=True)


def forecast_property_type(tx: pd.DataFrame, property_type: str,
                           periods: int = 4, group: str = "Sales") -> pd.DataFrame:
    """Return historical + forecast rows with yhat and confidence bounds."""
    from prophet import Prophet

    df = build_series(tx, property_type, group)
    if len(df) < 4:
        raise ValueError(f"not enough history to forecast {property_type}")

    model = Prophet(interval_width=0.80, yearly_seasonality=False,
                    weekly_seasonality=False, daily_seasonality=False)
    model.fit(df)
    future = model.make_future_dataframe(periods=periods, freq="QS")
    fc = model.predict(future)
    out = fc[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    out["property_type"] = property_type
    out = out.merge(df, on="ds", how="left").rename(columns={"y": "actual"})
    out["is_forecast"] = out["actual"].isna()
    return out


def forecast_all(tx: pd.DataFrame, periods: int = 4, group: str = "Sales") -> pd.DataFrame:
    frames = []
    for ptype in ["Units", "Building", "Land", "Villa"]:
        try:
            frames.append(forecast_property_type(tx, ptype, periods, group))
        except Exception as exc:  # noqa: BLE001
            log.warning("forecast skipped for %s: %s", ptype, exc)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
