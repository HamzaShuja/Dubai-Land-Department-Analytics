"""Ingestion layer.

Reads the raw Dubai Pulse / DLD sources, applies the Arabic->English
translation, and runs every record through the Pydantic validation layer. The
``DATA_SOURCE`` flag chooses the backend: ``xlsx`` (phase 1, local workbooks) or
``api`` (phase 2, live DLD API). When the API key arrives and ``DATA_SOURCE=api``
the projects loader auto-switches with no other code change; until then it
transparently falls back to the XLSX so the platform always runs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from .config import Settings, get_settings, DataSource
from .logging_config import get_logger
from . import translation as T
from .schemas import TransactionRecord, ProjectRecord, ValidationReport

log = get_logger(__name__)


@dataclass
class IngestResult:
    transactions: pd.DataFrame
    projects: pd.DataFrame
    reports: list[ValidationReport]


# --------------------------------------------------------------------------- #
# Raw readers
# --------------------------------------------------------------------------- #
def read_transactions_xlsx(path) -> pd.DataFrame:
    log.info("Reading transactions workbook: %s", path)
    df = pd.read_excel(path)
    df = df.rename(columns=T.TRANSACTIONS_COLUMN_MAP)

    # Derive quarter_number from the Arabic-mirrored quarter if absent.
    if "quarter_number" not in df.columns:
        df["quarter_number"] = df["quarter"].map(T.QUARTER_TO_INT)
    df["quarter_number"] = (
        pd.to_numeric(df["quarter_number"], errors="coerce")
        .fillna(df["quarter"].map(T.QUARTER_TO_INT))
    )

    keep = [
        "year", "quarter", "quarter_number", "property_type",
        "transaction_group", "measure", "amount",
    ]
    df = df[[c for c in keep if c in df.columns]].copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df


def read_projects_xlsx(path) -> pd.DataFrame:
    log.info("Reading projects workbook: %s", path)
    df = pd.read_excel(path)

    rename = {
        "project_type_en": "project_type",
        "project_type_ar": "project_type_ar",
    }
    df = df.rename(columns=rename)
    if "project_type" not in df.columns and "project_type_ar" in df.columns:
        df["project_type"] = df["project_type_ar"]

    df["project_status"] = df["project_status"].map(T.normalise_status)

    cols = [
        "project_id", "project_name", "master_project_en", "area_id", "area_name_en",
        "developer_id", "developer_name", "master_developer_name",
        "project_status", "project_type", "percent_completed",
        "no_of_units", "no_of_buildings", "no_of_villas", "no_of_lands",
        "project_start_date", "project_end_date",
    ]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols].copy()


def fetch_projects_api(settings: Settings) -> Optional[pd.DataFrame]:
    """Phase-2 hook: fetch projects from the live DLD API.

    Returns a DataFrame in the same shape as ``read_projects_xlsx`` or ``None``
    if the API is not reachable / not configured, so the caller can fall back to
    the local workbook. Implemented defensively so enabling the API never breaks
    a running pipeline.
    """
    import requests

    url = f"{settings.dld_api_base.rstrip('/')}/projects"
    headers = {"Authorization": f"Bearer {settings.dld_api_key}"}
    try:
        log.info("Fetching projects from DLD API: %s", url)
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        records = payload.get("data", payload) if isinstance(payload, dict) else payload
        df = pd.DataFrame(records)
        df["project_status"] = df.get("project_status", pd.Series(dtype=str)).map(
            T.normalise_status
        )
        log.info("DLD API returned %d project rows", len(df))
        return df
    except Exception as exc:  # noqa: BLE001 — defensive: never crash on API
        log.warning("DLD API fetch failed (%s); falling back to XLSX.", exc)
        return None


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def _validate(df: pd.DataFrame, model, dataset: str) -> tuple[pd.DataFrame, ValidationReport]:
    accepted, errors = [], []
    for i, row in enumerate(df.to_dict(orient="records")):
        try:
            accepted.append(model(**row).model_dump())
        except Exception as exc:  # noqa: BLE001
            if len(errors) < 25:  # cap the stored sample
                errors.append(f"row {i}: {exc}")
    report = ValidationReport(
        dataset=dataset, total=len(df), accepted=len(accepted),
        rejected=len(df) - len(accepted), errors=errors,
    )
    log.info(
        "Validation [%s]: %d/%d accepted (%.1f%%)",
        dataset, report.accepted, report.total, report.acceptance_rate * 100,
    )
    return pd.DataFrame(accepted), report


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def ingest(settings: Settings | None = None) -> IngestResult:
    settings = settings or get_settings()

    tx_raw = read_transactions_xlsx(settings.transactions_path)

    proj_raw = None
    if settings.api_ready:
        from .dda_client import DDAClient
        proj_raw = DDAClient(settings).fetch_projects()
    if proj_raw is None:
        proj_raw = read_projects_xlsx(settings.projects_path)

    tx_clean, tx_report = _validate(tx_raw, TransactionRecord, "transactions")
    proj_clean, proj_report = _validate(proj_raw, ProjectRecord, "projects")

    return IngestResult(
        transactions=tx_clean,
        projects=proj_clean,
        reports=[tx_report, proj_report],
    )
