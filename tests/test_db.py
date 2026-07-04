"""PostgreSQL schema + loader (round-trip and idempotency)."""
from sqlalchemy import text

from realestate import db


def test_schema_and_load_roundtrip(pg_engine, transactions, projects):
    db.create_schema(pg_engine, drop=True)
    n_tx = db.load_transactions(pg_engine, transactions)
    n_pr = db.load_projects(pg_engine, projects)
    assert n_tx == len(transactions)
    assert n_pr == len(projects)

    with pg_engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM transactions")).scalar() == n_tx
        assert c.execute(text("SELECT count(*) FROM projects")).scalar() == n_pr


def test_load_is_idempotent(pg_engine, transactions, projects):
    db.create_schema(pg_engine)
    db.load_projects(pg_engine, projects)
    db.load_projects(pg_engine, projects)  # second load truncates first
    with pg_engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM projects")).scalar() == len(projects)


def test_nulls_preserved(pg_engine, projects):
    db.create_schema(pg_engine)
    db.load_projects(pg_engine, projects)
    expected_nulls = int(projects["developer_id"].isna().sum())
    with pg_engine.connect() as c:
        got = c.execute(text("SELECT count(*) FROM projects WHERE developer_id IS NULL")).scalar()
    assert got == expected_nulls
