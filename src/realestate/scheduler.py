"""APScheduler-based daily refresh.

Runs the full ETL pipeline and rebuilds model artifacts every day at the
configured hour. Activates automatically once the DLD API key is present
(``DATA_SOURCE=api``) but also works in XLSX mode. Invoke with:
    python -m realestate.scheduler
"""
from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import get_settings
from .logging_config import configure_logging, get_logger
from .pipeline import run_pipeline
from .build_artifacts import main as build_artifacts

log = get_logger(__name__)


def refresh_job() -> None:
    """One full refresh cycle: reload data, retrain artifacts."""
    settings = get_settings()
    log.info("Scheduled refresh starting (source=%s)", settings.data_source.value)
    try:
        result = run_pipeline(settings, create=True)
        build_artifacts()
        log.info("Scheduled refresh complete: %d transactions, %d projects",
                 result.transactions_loaded, result.projects_loaded)
    except Exception:  # noqa: BLE001
        log.exception("Scheduled refresh failed")


def build_scheduler() -> BlockingScheduler:
    settings = get_settings()
    scheduler = BlockingScheduler(timezone="Asia/Dubai")
    scheduler.add_job(
        refresh_job,
        CronTrigger(hour=settings.refresh_hour, minute=0),
        id="daily_refresh",
        name="Daily data + model refresh",
        replace_existing=True,
    )
    log.info("Scheduler configured: daily refresh at %02d:00 Asia/Dubai",
             settings.refresh_hour)
    return scheduler


def main() -> None:
    configure_logging(get_settings().log_level)
    scheduler = build_scheduler()
    log.info("Starting scheduler (Ctrl+C to exit)")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped")


if __name__ == "__main__":
    main()
