"""Test configuration and fixtures."""

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

from myunla.models.config import ServiceConfig


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_config_path() -> Path:
    """Return path to sample configuration file."""
    return Path(__file__).parent / "fixtures" / "sample_config.yaml"


@pytest.fixture
def sample_openapi_spec() -> Dict[str, Any]:
    """Return sample OpenAPI specification."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Sample API", "version": "1.0.0"},
        "paths": {
            "/users/{user_id}": {
                "get": {
                    "operationId": "get_user",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "User details",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "email": {"type": "string"},
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }


@pytest.fixture
def sample_config_data() -> Dict[str, Any]:
    """Sample configuration data for tests."""
    return {
        "version": "1.0",
        "services": [
            {
                "name": "test_service",
                "description": "Test service",
                "base_url": "https://api.example.com",
                "endpoints": [
                    {
                        "path": "/users",
                        "method": "GET",
                        "mcp_type": "tool",
                        "mcp_name": "list_users",
                        "description": "List users",
                    }
                ],
            }
        ],
    }


@pytest.fixture
def sample_service_config() -> ServiceConfig:
    """Sample service configuration."""
    from myunla.models.config import (
        EndpointConfig,
        HTTPMethod,
        MCPType,
        ServiceConfig,
    )

    return ServiceConfig(
        name="test_service",
        description="Test service",
        base_url="https://api.example.com",
        endpoints=[
            EndpointConfig(
                path="/users",
                method=HTTPMethod.GET,
                mcp_type=MCPType.TOOL,
                mcp_name="list_users",
                description="List users",
            )
        ],
    )


@pytest.fixture
def mock_http_client() -> Any:
    """Mock HTTP client for testing."""
    from unittest.mock import AsyncMock

    mock_client = AsyncMock()
    mock_client.get.return_value = AsyncMock(
        status_code=200, json=lambda: [{"id": 1, "name": "test"}]
    )
    mock_client.post.return_value = AsyncMock(
        status_code=201, json=lambda: {"id": 1, "name": "created"}
    )
    mock_client.request.return_value = AsyncMock(
        status_code=200, json=lambda: {"result": "success"}
    )
    return mock_client


@pytest.fixture
def mock_config_manager() -> Any:
    """Mock configuration manager."""
    from unittest.mock import Mock

    from myunla.models.config import GatewayConfig

    mock_manager = Mock()
    mock_manager.get_config.return_value = GatewayConfig()
    mock_manager.config_path = Path("test_config.yaml")
    return mock_manager
