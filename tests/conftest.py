"""Shared pytest fixtures.

Data fixtures load the real Dubai Pulse / DLD workbooks shipped in ``input/``.
The database fixture prefers the configured PostgreSQL (the CI service), and
falls back to an ephemeral local Postgres via ``pgserver`` for offline runs.
Tests needing a database are skipped only if neither is available.
"""
from __future__ import annotations

import tempfile

import pytest
from sqlalchemy import text

from realestate.ingestion import ingest
from realestate.cleaning import clean_transactions, clean_projects
from realestate import db
from realestate.config import get_settings


@pytest.fixture(scope="session")
def ingested():
    return ingest()


@pytest.fixture(scope="session")
def transactions(ingested):
    return clean_transactions(ingested.transactions)


@pytest.fixture(scope="session")
def projects(ingested):
    return clean_projects(ingested.projects)


@pytest.fixture(scope="session")
def pg_engine():
    # 1) Try the configured database (CI postgres service).
    try:
        eng = db.get_engine(get_settings().sqlalchemy_url)
        with eng.connect() as c:
            c.execute(text("SELECT 1"))
        yield eng
        eng.dispose()
        return
    except Exception:
        pass
    # 2) Fall back to an ephemeral local Postgres.
    try:
        import pgserver
    except ImportError:
        pytest.skip("no PostgreSQL available (configured DB unreachable, pgserver not installed)")
    srv = pgserver.get_server(tempfile.mkdtemp())
    eng = db.get_engine("postgresql+psycopg://" + srv.get_uri().split("://", 1)[1])
    yield eng
    eng.dispose()
    srv.cleanup()


@pytest.fixture(scope="session")
def trained_model(projects):
    from realestate.models import lgbm_model
    return lgbm_model.train(projects, register=False)
