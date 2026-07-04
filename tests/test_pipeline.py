"""End-to-end ETL pipeline + data-access round trip."""
from realestate.pipeline import run_pipeline
from realestate import data_access


def test_run_pipeline_loads_db(pg_engine):
    result = run_pipeline(engine=pg_engine, create=True, drop=True)
    assert result.transactions_loaded == 696
    assert result.projects_loaded > 3000
    # Validation reports surfaced.
    assert all(r.acceptance_rate == 1.0 for r in result.validation)


def test_data_access_reads_back(pg_engine):
    run_pipeline(engine=pg_engine, create=True, drop=True)
    tx = data_access.load_transactions(pg_engine)
    pr = data_access.load_projects(pg_engine)
    assert len(tx) == 696
    assert len(pr) > 3000
    assert {"period", "period_label"}.issubset(tx.columns)
    assert {"is_ready", "total_assets"}.issubset(pr.columns)
