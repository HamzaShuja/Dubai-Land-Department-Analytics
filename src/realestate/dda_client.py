"""DDA iPaaS (Dubai Data portal) API client for the real-estate projects dataset.

Implements the OAuth2 client-credentials flow used by the Dubai Digital Authority
iPaaS gateway: exchange client_id/client_secret for a bearer token, then call the
dataset endpoint with the token plus the ``x-DDA-SecurityApplicationIdentifier``
header and the Application Id. All endpoints and credentials come from the
environment (never hard-coded), so the same code runs in STG and PROD.

The client is defensive: any failure returns ``None`` so the pipeline falls back
to the local workbook and never breaks. Response parsing tolerates the common
gateway envelopes (a bare list, ``{"data": [...]}``, ``{"result": [...]}``,
``{"items": [...]}``) and simple page-based pagination.
"""
from __future__ import annotations

import time
from typing import Optional

import pandas as pd

from .config import Settings, get_settings
from .logging_config import get_logger
from . import translation as T

log = get_logger(__name__)

# Candidate keys that may hold the record array in the gateway response.
_ENVELOPE_KEYS = ("data", "result", "results", "items", "records", "payload")


class DDAClient:
    def __init__(self, settings: Optional[Settings] = None):
        self.s = settings or get_settings()
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0

    # ---- Auth --------------------------------------------------------------
    def _fetch_token(self) -> str:
        import requests

        data = {
            "grant_type": "client_credentials",
            "client_id": self.s.dda_client_id,
            "client_secret": self.s.dda_client_secret,
        }
        if self.s.dda_scope:
            data["scope"] = self.s.dda_scope
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        # Some gateways also expect the security identifier on the token call.
        if self.s.dda_security_app_id:
            headers["x-DDA-SecurityApplicationIdentifier"] = self.s.dda_security_app_id

        log.info("Requesting DDA iPaaS token (env=%s)", self.s.dda_env)
        resp = requests.post(self.s.dda_token_url, data=data, headers=headers, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        token = payload.get("access_token") or payload.get("accessToken")
        if not token:
            raise RuntimeError(f"no access_token in token response keys={list(payload)}")
        expires_in = float(payload.get("expires_in", 3000))
        self._token = token
        self._token_expiry = time.time() + expires_in - 60  # refresh 1 min early
        return token

    def _token_valid(self) -> bool:
        return bool(self._token) and time.time() < self._token_expiry

    def token(self) -> str:
        if not self._token_valid():
            self._fetch_token()
        return self._token  # type: ignore[return-value]

    def _auth_headers(self) -> dict:
        headers = {
            "Authorization": f"Bearer {self.token()}",
            "Accept": "application/json",
        }
        if self.s.dda_security_app_id:
            headers["x-DDA-SecurityApplicationIdentifier"] = self.s.dda_security_app_id
        if self.s.dda_application_id:
            # Header name per the DDA onboarding contract; adjust if different.
            headers["x-DDA-ApplicationId"] = self.s.dda_application_id
        return headers

    # ---- Data --------------------------------------------------------------
    @staticmethod
    def _extract_records(payload) -> list[dict]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for k in _ENVELOPE_KEYS:
                v = payload.get(k)
                if isinstance(v, list):
                    return v
            # Nested one level (e.g. {"data": {"items": [...]}})
            for v in payload.values():
                if isinstance(v, dict):
                    for k in _ENVELOPE_KEYS:
                        if isinstance(v.get(k), list):
                            return v[k]
        return []

    def fetch_projects_raw(self) -> list[dict]:
        """Fetch all project records, following simple page-based pagination."""
        import requests

        records: list[dict] = []
        page = 1
        while True:
            params = {"page": page, "pageSize": self.s.dda_page_size,
                      "limit": self.s.dda_page_size,
                      "offset": (page - 1) * self.s.dda_page_size}
            resp = requests.get(self.s.dda_projects_url, headers=self._auth_headers(),
                                params=params, timeout=60)
            resp.raise_for_status()
            batch = self._extract_records(resp.json())
            if not batch:
                break
            records.extend(batch)
            if len(batch) < self.s.dda_page_size:
                break
            page += 1
            if page > 1000:  # safety guard
                break
        log.info("DDA iPaaS returned %d project records", len(records))
        return records

    def fetch_projects(self) -> Optional[pd.DataFrame]:
        """Fetch projects as a DataFrame shaped like the XLSX loader, or None on
        any failure (caller falls back to the local workbook)."""
        try:
            records = self.fetch_projects_raw()
            if not records:
                log.warning("DDA iPaaS returned no records; falling back to XLSX.")
                return None
            df = pd.DataFrame(records)
            df = _normalise_api_projects(df)
            return df
        except Exception as exc:  # noqa: BLE001 — never break the pipeline
            log.warning("DDA iPaaS fetch failed (%s); falling back to XLSX.", exc)
            return None


# Map likely API field names to the internal schema. The DLD projects dataset
# generally uses these snake_case names; add aliases here if the live response
# differs (a one-line change once we see a sample payload).
_API_FIELD_ALIASES = {
    "projectId": "project_id", "projectName": "project_name",
    "areaId": "area_id", "areaNameEn": "area_name_en", "areaNameEN": "area_name_en",
    "developerId": "developer_id", "developerName": "developer_name",
    "masterDeveloperName": "master_developer_name",
    "projectStatus": "project_status", "projectType": "project_type",
    "percentCompleted": "percent_completed",
    "noOfUnits": "no_of_units", "noOfBuildings": "no_of_buildings",
    "noOfVillas": "no_of_villas", "noOfLands": "no_of_lands",
    "projectStartDate": "project_start_date", "projectEndDate": "project_end_date",
}


def _normalise_api_projects(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=_API_FIELD_ALIASES)
    if "project_type" not in df.columns and "project_type_ar" in df.columns:
        df["project_type"] = df["project_type_ar"]
    if "project_status" in df.columns:
        df["project_status"] = df["project_status"].map(T.normalise_status)
    cols = ["project_id", "project_name", "area_id", "area_name_en",
            "developer_id", "developer_name", "master_developer_name",
            "project_status", "project_type", "percent_completed",
            "no_of_units", "no_of_buildings", "no_of_villas", "no_of_lands",
            "project_start_date", "project_end_date"]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols].copy()
