"""End-to-end ETL orchestration.

Wires together ingestion -> validation -> cleaning -> database load and emits a
structured summary for every run. This is the single entry point used by the
CLI, the scheduler, and the test-suite.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.engine import Engine

from .config import Settings, get_settings
from .logging_config import configure_logging, get_logger
from .ingestion import ingest
from .cleaning import clean_transactions, clean_projects
from . import db

log = get_logger(__name__)


@dataclass
class PipelineResult:
    transactions_loaded: int = 0
    projects_loaded: int = 0
    validation: list = field(default_factory=list)


def run_pipeline(
    settings: Optional[Settings] = None,
    engine: Optional[Engine] = None,
    create: bool = True,
    drop: bool = False,
) -> PipelineResult:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    log.info("=== Pipeline run start (source=%s) ===", settings.data_source.value)

    ingested = ingest(settings)
    tx = clean_transactions(ingested.transactions)
    pr = clean_projects(ingested.projects)

    engine = engine or db.get_engine()
    if create:
        db.create_schema(engine, drop=drop)

    n_tx = db.load_transactions(engine, tx)
    n_pr = db.load_projects(engine, pr)

    log.info("=== Pipeline run complete: %d transactions, %d projects ===", n_tx, n_pr)
    return PipelineResult(
        transactions_loaded=n_tx,
        projects_loaded=n_pr,
        validation=ingested.reports,
    )


def main() -> None:
    # drop=True keeps the schema in sync with the code (the load is a full
    # refresh, so recreating tables loses nothing).
    result = run_pipeline(create=True, drop=True)
    for r in result.validation:
        print(f"{r.dataset}: {r.accepted}/{r.total} accepted ({r.acceptance_rate*100:.1f}%)")
    print(f"Loaded {result.transactions_loaded} transactions, {result.projects_loaded} projects")


if __name__ == "__main__":
    main()
