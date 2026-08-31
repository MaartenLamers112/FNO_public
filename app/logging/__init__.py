"""Centrale applicatielogging."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask


def configure_logging(app: Flask) -> None:
    """Configureer console- en roterende bestandslogging."""

    level = getattr(logging, app.config["LOG_LEVEL"], logging.INFO)
    app.logger.setLevel(level)

    log_directory = Path(app.config["LOG_DIR"])
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file = (log_directory / "application.log").resolve()
    if any(
        isinstance(handler, RotatingFileHandler)
        and Path(handler.baseFilename).resolve() == log_file
        for handler in app.logger.handlers
    ):
        return

    handler = RotatingFileHandler(
        log_file,
        maxBytes=app.config["LOG_MAX_BYTES"],
        backupCount=app.config["LOG_BACKUP_COUNT"],
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    )
    app.logger.addHandler(handler)
