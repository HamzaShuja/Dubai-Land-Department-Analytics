"""Pydantic validation layer.

Every record is validated through these models *before* it can reach the
database. Invalid rows are collected and reported rather than silently dropped,
so each pipeline run produces an auditable count of accepted vs rejected rows.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


def _is_nan(v) -> bool:
    return isinstance(v, float) and v != v


class TransactionRecord(BaseModel):
    """One row of the aggregated quarterly market-statistics dataset."""

    model_config = ConfigDict(str_strip_whitespace=True)

    year: int = Field(ge=1990, le=2100)
    quarter: str
    quarter_number: int = Field(ge=1, le=4)
    property_type: str
    transaction_group: str   # Sales / Mortgages / Other
    measure: str             # Value / Number
    amount: float = Field(ge=0)

    @field_validator("property_type")
    @classmethod
    def _known_type(cls, v: str) -> str:
        allowed = {"Units", "Building", "Land", "Villa"}
        if v not in allowed:
            raise ValueError(f"unknown property_type: {v!r}")
        return v

    @field_validator("transaction_group")
    @classmethod
    def _known_group(cls, v: str) -> str:
        allowed = {"Sales", "Mortgages", "Other"}
        if v not in allowed:
            raise ValueError(f"unknown transaction_group: {v!r}")
        return v

    @field_validator("measure")
    @classmethod
    def _known_measure(cls, v: str) -> str:
        if v not in {"Value", "Number"}:
            raise ValueError(f"unknown measure: {v!r}")
        return v


class ProjectRecord(BaseModel):
    """One DLD real-estate project."""

    model_config = ConfigDict(str_strip_whitespace=True)

    project_id: int
    project_name: Optional[str] = None
    master_project_en: Optional[str] = None
    area_id: Optional[int] = None
    area_name_en: str
    developer_id: Optional[int] = None
    developer_name: str
    master_developer_name: Optional[str] = None
    project_status: str
    project_type: Optional[str] = None
    percent_completed: float = Field(ge=0, le=100)
    no_of_units: int = Field(ge=0)
    no_of_buildings: int = Field(ge=0)
    no_of_villas: int = Field(ge=0)
    no_of_lands: int = Field(ge=0)
    project_start_date: Optional[datetime] = None
    project_end_date: Optional[datetime] = None

    @field_validator("area_id", "developer_id", "area_id", mode="before")
    @classmethod
    def _coerce_optional_int(cls, v):
        """NaN / blank optional IDs become None instead of rejecting the row."""
        if v is None or _is_nan(v) or v == "":
            return None
        return int(float(v))

    @field_validator("project_name", "master_project_en", "master_developer_name", "project_type", mode="before")
    @classmethod
    def _coerce_optional_str(cls, v):
        if v is None or _is_nan(v) or str(v).strip() == "":
            return None
        return str(v).strip()

    @field_validator("project_start_date", "project_end_date", mode="before")
    @classmethod
    def _coerce_optional_dt(cls, v):
        if v is None or _is_nan(v) or str(v).strip() in ("", "NaT"):
            return None
        return v

    @field_validator("area_name_en", "developer_name")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("must not be empty")
        return v

    @field_validator(
        "no_of_units", "no_of_buildings", "no_of_villas", "no_of_lands",
        mode="before",
    )
    @classmethod
    def _coerce_counts(cls, v):
        if v is None or _is_nan(v):
            return 0
        return int(float(v))

    @field_validator("percent_completed", mode="before")
    @classmethod
    def _coerce_pct(cls, v):
        if v is None or _is_nan(v):
            return 0.0
        return min(max(float(v), 0.0), 100.0)


class ValidationReport(BaseModel):
    """Outcome of validating a batch of raw records."""

    dataset: str
    total: int
    accepted: int
    rejected: int
    errors: list[str] = Field(default_factory=list)

    @property
    def acceptance_rate(self) -> float:
        return self.accepted / self.total if self.total else 0.0
