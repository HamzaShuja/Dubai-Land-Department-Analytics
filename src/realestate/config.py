"""Central configuration.

Loads settings from the environment / .env file using pydantic-settings so
every value is validated and typed before the pipeline starts. The
``DATA_SOURCE`` flag is the single switch that moves the platform from the
local Dubai Pulse XLSX files (phase 1) to the live DLD API (phase 2): drop the
API key into ``.env`` and set ``DATA_SOURCE=api`` and the ingestion layer
auto-switches with no code changes.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = three levels up from this file (src/realestate/config.py).
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class DataSource(str, Enum):
    XLSX = "xlsx"
    API = "api"


class Settings(BaseSettings):
    """Validated runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/realestate",
        description="SQLAlchemy/psycopg PostgreSQL DSN.",
    )
    data_source: DataSource = DataSource.XLSX

    dld_api_key: str = ""
    dld_api_base: str = "https://api.dubailand.gov.ae"

    # --- DDA iPaaS (Dubai Data portal) live API for the projects dataset ---
    dda_token_url: str = ""          # OAuth2 client-credentials token endpoint
    dda_projects_url: str = ""       # projects dataset endpoint
    dda_client_id: str = ""
    dda_client_secret: str = ""
    dda_security_app_id: str = ""    # x-DDA-SecurityApplicationIdentifier header
    dda_application_id: str = ""     # Application Id
    dda_scope: str = ""              # optional OAuth scope
    dda_env: str = "STG"
    dda_page_size: int = 1000

    transactions_xlsx: str = "input/Real_Estate_Transactions_2026-06-23.xlsx"
    projects_xlsx: str = "input/projects_2026-05-21_02-07-22_1.xlsx"

    refresh_hour: int = Field(default=3, ge=0, le=23)
    mlflow_tracking_uri: str = "sqlite:///artifacts/mlflow.db"
    log_level: str = "INFO"

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalise_dsn(cls, v: str) -> str:
        """Accept the slightly non-standard ``DB:postgresql://...`` form the
        Dubai Pulse handover file ships with, and SQLAlchemy's preferred
        ``postgresql+psycopg://`` driver prefix."""
        if v is None:
            return v
        v = str(v).strip()
        # Tolerate a stray "DB:" / "DB=" prefix from the raw handover file.
        for prefix in ("DB:", "DB="):
            if v.startswith(prefix):
                v = v[len(prefix):].strip()
        return v

    @property
    def sqlalchemy_url(self) -> str:
        """Force the psycopg (v3) driver for SQLAlchemy."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url

    def resolve(self, relative: str) -> Path:
        """Resolve a path that may be relative to the project root."""
        p = Path(relative)
        return p if p.is_absolute() else (PROJECT_ROOT / p)

    @property
    def transactions_path(self) -> Path:
        return self.resolve(self.transactions_xlsx)

    @property
    def projects_path(self) -> Path:
        return self.resolve(self.projects_xlsx)

    @property
    def api_ready(self) -> bool:
        """True only when DATA_SOURCE=api AND the DDA iPaaS client is fully
        configured (credentials + both endpoint URLs). Otherwise the pipeline
        safely falls back to the local XLSX so it never breaks."""
        return (
            self.data_source is DataSource.API
            and bool(self.dda_client_id.strip())
            and bool(self.dda_client_secret.strip())
            and bool(self.dda_token_url.strip())
            and bool(self.dda_projects_url.strip())
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
