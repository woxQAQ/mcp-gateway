"""Configuration management for MCP Gateway."""

import asyncio
import json
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

if TYPE_CHECKING:
    from watchdog.observers.api import BaseObserver

from myunla.models.config import (
    EndpointConfig,
    GatewayConfig,
    ServiceConfig,
    Settings,
)
from myunla.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigReloadHandler(FileSystemEventHandler):
    """Handler for configuration file changes."""

    def __init__(self, callback: Callable[[], None]) -> None:
        self.callback = callback
        self._debounce_timer: asyncio.TimerHandle | None = None
        self._debounce_delay = 1.0  # seconds

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory and str(event.src_path).endswith(
            (".yaml", ".yml", ".json")
        ):
            logger.info(f"Configuration file modified: {event.src_path!r}")

            # Debounce rapid file changes
            if self._debounce_timer:
                self._debounce_timer.cancel()

            self._debounce_timer = asyncio.get_event_loop().call_later(
                self._debounce_delay, self._trigger_reload
            )

    def _trigger_reload(self) -> None:
        """Trigger configuration reload."""
        logger.info("Triggering configuration reload")
        self.callback()
        self._debounce_timer = None


class ConfigManager:
    """Configuration manager with hot reload support."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = Path(config_path)
        self.config: GatewayConfig | None = None
        self.settings = Settings()
        self._observers: dict[Path, BaseObserver] = {}
        self._reload_callbacks: list[Callable[[GatewayConfig], None]] = []

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )

        self.load_config()
        self._start_file_watcher()

    def load_config(self) -> GatewayConfig:
        """Load configuration from file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                if self.config_path.suffix.lower() in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)

            self.config = GatewayConfig(**data)
            logger.info(
                f"Configuration loaded successfully from {self.config_path}"
            )

            # Notify callbacks
            for callback in self._reload_callbacks:
                try:
                    callback(self.config)
                except Exception as e:
                    logger.error(f"Error in config reload callback: {e}")

            return self.config

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    def get_config(self) -> GatewayConfig:
        """Get current configuration."""
        if self.config is None:
            return self.load_config()
        return self.config

    def add_reload_callback(
        self, callback: Callable[[GatewayConfig], None]
    ) -> None:
        """Add a callback to be called when configuration is reloaded."""
        self._reload_callbacks.append(callback)

    def _start_file_watcher(self) -> None:
        """Start file system watcher for configuration changes."""
        try:
            observer = Observer()

            def _reload_callback() -> None:
                self.load_config()

            handler = ConfigReloadHandler(_reload_callback)
            observer.schedule(
                handler, str(self.config_path.parent), recursive=False
            )
            observer.start()
            self._observers[self.config_path.parent] = observer
            logger.info(
                f"Started watching configuration file: {self.config_path}"
            )
        except Exception as e:
            logger.warning(f"Failed to start file watcher: {e}")

    def stop(self) -> None:
        """Stop all file watchers."""
        for observer in self._observers.values():
            observer.stop()
            observer.join()
        self._observers.clear()
        logger.info("Configuration file watchers stopped")

    def get_service_config(self, service_name: str) -> ServiceConfig | None:
        """Get configuration for a specific service."""
        if not self.config:
            return None

        for service in self.config.services:
            if service.name == service_name:
                return service
        return None

    def get_endpoint_config(
        self, service_name: str, endpoint_name: str
    ) -> EndpointConfig | None:
        """Get configuration for a specific endpoint."""
        service = self.get_service_config(service_name)
        if not service:
            return None

        for endpoint in service.endpoints:
            if endpoint.mcp_name == endpoint_name:
                return endpoint
        return None

    def reload(self) -> None:
        """Manually trigger configuration reload."""
        logger.info("Manual configuration reload triggered")
        self.load_config()

    def validate_config(self) -> bool:
        """Validate current configuration."""
        try:
            if not self.config:
                return False

            # Validate service configurations
            for service in self.config.services:
                if not service.name or not service.base_url:
                    logger.error(
                        f"Invalid service configuration: {service.name}"
                    )
                    return False

                # Validate endpoint configurations
                for endpoint in service.endpoints:
                    if not endpoint.mcp_name or not endpoint.path:
                        logger.error(
                            f"Invalid endpoint configuration: {endpoint.mcp_name}"
                        )
                        return False

            logger.info("Configuration validation passed")
            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
