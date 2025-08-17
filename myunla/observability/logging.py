"""Logging configuration and utilities."""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any

import structlog


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    output_file: Path | None = None,
) -> None:
    """Setup structured logging for the application."""

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            (
                structlog.processors.JSONRenderer()
                if format_type == "json"
                else structlog.dev.ConsoleRenderer()
            ),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": "%(asctime)s %(name)s %(levelname)s %(message)s",
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "json" if format_type == "json" else "standard",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": level,
                "propagate": False,
            },
            "myunla": {
                "handlers": ["console"],
                "level": level,
                "propagate": False,
            },
        },
    }

    # Add file handler if output_file is specified
    if output_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": "json" if format_type == "json" else "standard",
            "filename": str(output_file),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        }
        config["loggers"][""]["handlers"].append("file")
        config["loggers"]["myunla"]["handlers"].append("file")

    logging.config.dictConfig(config)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    logger = structlog.get_logger(name)
    return logger


class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation ID to log records."""

    def __init__(self, name: str = ""):
        super().__init__(name)
        self.correlation_id: str | None = None

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        if self.correlation_id:
            record.correlation_id = self.correlation_id
        return True

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set the correlation ID for this filter."""
        self.correlation_id = correlation_id


def get_correlation_logger(
    name: str, correlation_id: str | None = None
) -> structlog.stdlib.BoundLogger:
    """Get a logger with correlation ID support."""
    logger = get_logger(name)

    if correlation_id:
        logger = logger.bind(correlation_id=correlation_id)

    return logger
