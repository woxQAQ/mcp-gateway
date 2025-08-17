"""
MCP Gateway Entry Point

Main entry point for the MyUnla MCP Gateway application.
"""

import asyncio
import logging
import sys
from pathlib import Path

from myunla.config.manager import ConfigManager
from myunla.core.gateway import MCPGateway


def main() -> None:
    """Main entry point for the MCP Gateway."""
    try:
        # Setup basic logging first
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logger = logging.getLogger(__name__)

        config_path = Path("config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)

        config_manager = ConfigManager(config_path)
        gateway = MCPGateway(config_manager)

        logger.info("Starting MCP Gateway...")
        asyncio.run(gateway.run())

    except KeyboardInterrupt:
        logging.info("Shutting down MCP Gateway...")
    except Exception as e:
        logging.error(f"Failed to start MCP Gateway: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
