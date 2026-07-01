"""
Logging setup for Sembako Dashboard.
Provides centralized loggers with rotating file handlers.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import LOGS_DIR, LOG_FORMAT, LOG_DATE_FORMAT


def _ensure_logs_dir():
    """Ensure the logs directory exists."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _create_rotating_handler(
    filename: str,
    level: int = logging.DEBUG,
) -> RotatingFileHandler:
    """Create a RotatingFileHandler with standard settings."""
    _ensure_logs_dir()
    handler = RotatingFileHandler(
        LOGS_DIR / filename,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    handler.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    handler.setFormatter(formatter)
    return handler


def _create_stream_handler() -> logging.StreamHandler:
    """Create a stderr stream handler for console output."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    handler.setFormatter(formatter)
    return handler


def setup_app_logger() -> logging.Logger:
    """Set up the main application logger."""
    logger = logging.getLogger("sembako")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        logger.addHandler(_create_rotating_handler("app.log"))
        logger.addHandler(_create_stream_handler())

    return logger


def setup_scraper_logger(name: str) -> logging.Logger:
    """Set up a scraper-specific logger."""
    logger = logging.getLogger(f"sembako.scraper.{name}")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        logger.addHandler(_create_rotating_handler("scrape.log"))
        logger.addHandler(_create_stream_handler())

    return logger


def setup_update_logger() -> logging.Logger:
    """Set up the data-update logger."""
    logger = logging.getLogger("sembako.update")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        logger.addHandler(_create_rotating_handler("update.log"))
        logger.addHandler(_create_stream_handler())

    return logger


def setup_dedup_logger() -> logging.Logger:
    """Set up the deduplication logger."""
    logger = logging.getLogger("sembako.dedup")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        logger.addHandler(_create_rotating_handler("dedup.log"))
        logger.addHandler(_create_stream_handler())

    return logger
