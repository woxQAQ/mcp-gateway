"""Logging utilities for MyUnla MCP Gateway."""

import logging
import logging.config
import sys


def setup_logging(
    level: str | int = "INFO",
    format_type: str = "text",
    service_name: str = "myunla-mcp-gateway",
) -> None:
    """Setup logging configuration."""

    if format_type == "json":
        log_format = '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
    else:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=level, format=log_format, stream=sys.stdout, force=True
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
