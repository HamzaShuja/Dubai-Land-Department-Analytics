"""PostgreSQL schema definition and loader.

Uses SQLAlchemy Core so the exact same code path runs against the local
Postgres used in tests and the Neon cloud instance used in production. The
loader performs an idempotent full refresh (truncate + append) inside a single
transaction, so a failed run never leaves the database half-populated.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, BigInteger, Float,
    String, Boolean, Date, text,
)
from sqlalchemy.engine import Engine

from .config import get_settings
from .logging_config import get_logger

log = get_logger(__name__)

metadata = MetaData()

transactions_table = Table(
    "transactions", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("year", Integer, nullable=False, index=True),
    Column("quarter", String(20), nullable=False),
    Column("quarter_number", Integer, nullable=False),
    Column("property_type", String(20), nullable=False, index=True),
    Column("transaction_group", String(20), nullable=False, index=True),
    Column("measure", String(20), nullable=False),
    Column("amount", Float, nullable=False),
    Column("period", Float, nullable=False, index=True),
    Column("period_label", String(10), nullable=False),
)

projects_table = Table(
    "projects", metadata,
    Column("project_id", BigInteger, primary_key=True),
    Column("project_name", String(512)),
    Column("master_project_en", String(256)),
    Column("area_id", BigInteger),
    Column("area_name_en", String(256), nullable=False, index=True),
    Column("developer_id", BigInteger),
    Column("developer_name", String(512), nullable=False, index=True),
    Column("master_developer_name", String(512)),
    Column("project_status", String(64), nullable=False, index=True),
    Column("project_type", String(128)),
    Column("percent_completed", Float, nullable=False),
    Column("no_of_units", Integer, nullable=False),
    Column("no_of_buildings", Integer, nullable=False),
    Column("no_of_villas", Integer, nullable=False),
    Column("no_of_lands", Integer, nullable=False),
    Column("project_start_date", Date),
    Column("project_end_date", Date),
    Column("planned_duration_days", Float),
    Column("is_ready", Boolean),
    Column("is_offplan", Boolean),
    Column("is_delivered", Boolean),
    Column("total_assets", Integer),
    Column("start_year", Float),
)

# Columns that physically exist in each table (used to align DataFrames).
_TX_COLS = [c.name for c in transactions_table.columns if c.name != "id"]
_PROJ_COLS = [c.name for c in projects_table.columns]


def get_engine(url: Optional[str] = None) -> Engine:
    url = url or get_settings().sqlalchemy_url
    return create_engine(url, pool_pre_ping=True, future=True)


def create_schema(engine: Engine, drop: bool = False) -> None:
    if drop:
        log.info("Dropping existing schema")
        metadata.drop_all(engine)
    metadata.create_all(engine)
    log.info("Schema ensured (tables: %s)", ", ".join(metadata.tables))


def _align(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Select the target columns and convert every missing value (NaN, NaT,
    pd.NA) into a real Python ``None`` so PostgreSQL receives proper NULLs."""
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            out[c] = None
    out = out[cols].astype(object)
    return out.where(pd.notnull(out), None)


def load_table(engine: Engine, df: pd.DataFrame, table: Table, cols: list[str]) -> int:
    aligned = _align(df, cols)
    records = aligned.to_dict(orient="records")
    with engine.begin() as conn:
        conn.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))
        if records:
            conn.execute(table.insert(), records)
    log.info("Loaded %d rows into %s", len(records), table.name)
    return len(records)


def load_transactions(engine: Engine, df: pd.DataFrame) -> int:
    return load_table(engine, df, transactions_table, _TX_COLS)


def load_projects(engine: Engine, df: pd.DataFrame) -> int:
    return load_table(engine, df, projects_table, _PROJ_COLS)
