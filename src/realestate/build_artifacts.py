"""Train and persist all model artifacts (LightGBM model, reference tables).

Run after the ETL pipeline so the API and dashboard have a model to serve:
    python -m realestate.build_artifacts
"""
from __future__ import annotations

from .config import get_settings
from .logging_config import configure_logging, get_logger
from .ingestion import ingest
from .cleaning import clean_projects
from .models import lgbm_model

log = get_logger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    log.info("Building model artifacts")
    projects = clean_projects(ingest(settings).projects)
    model = lgbm_model.train(projects, register=True)
    log.info("Artifacts built. Validation metrics: %s", model.metrics)


if __name__ == "__main__":
    main()
