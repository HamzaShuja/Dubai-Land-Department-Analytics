"""Read cleaned tables back out of PostgreSQL into DataFrames.

Analysis and modelling code depends only on these accessors, so it can run
against the live database or against in-memory DataFrames in tests.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy.engine import Engine

from . import db
from .config import get_settings


def _engine(engine: Engine | None) -> Engine:
    return engine or db.get_engine(get_settings().sqlalchemy_url)


def load_transactions(engine: Engine | None = None) -> pd.DataFrame:
    return pd.read_sql_table("transactions", _engine(engine))


def load_projects(engine: Engine | None = None) -> pd.DataFrame:
    return pd.read_sql_table("projects", _engine(engine))
