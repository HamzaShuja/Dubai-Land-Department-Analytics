"""Structured logging used across every pipeline run.

A single ``configure_logging`` call wires a consistent, parseable line format
to stdout and to a rotating per-run log file under ``artifacts/logs``. Every
module obtains its logger via ``get_logger(__name__)`` so log lines carry the
component that emitted them.
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import PROJECT_ROOT

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_configured = False


def configure_logging(level: str = "INFO") -> None:
    global _configured
    if _configured:
        return
    log_dir = PROJECT_ROOT / "artifacts" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level.upper())

    fmt = logging.Formatter(_LOG_FORMAT)

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    root.addHandler(stream)

    file_handler = RotatingFileHandler(
        log_dir / "pipeline.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # Quieten noisy third-party loggers.
    for noisy in ("cmdstanpy", "prophet", "matplotlib", "py4j"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
