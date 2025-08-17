"""Integration tests for MCP Gateway."""

from unittest.mock import patch

import pytest

from myunla.config.manager import ConfigManager
from myunla.core.gateway import MCPGateway
from myunla.models.config import (
    AuthenticationConfig,
    AuthType,
    EndpointConfig,
    GatewayConfig,
    HTTPMethod,
    MCPType,
    ServiceConfig,
)


@pytest.fixture
def test_config():
    """Test configuration for integration tests."""
    return GatewayConfig(
        version="1.0",
        services=[
            ServiceConfig(
                name="test_service",
                description="Test service",
                base_url="https://jsonplaceholder.typicode.com",
                endpoints=[
                    EndpointConfig(
                        path="/posts",
                        method=HTTPMethod.GET,
                        mcp_type=MCPType.TOOL,
                        mcp_name="list_posts",
                        description="List posts",
                    ),
                    EndpointConfig(
                        path="/posts/{post_id}",
                        method=HTTPMethod.GET,
                        mcp_type=MCPType.TOOL,
                        mcp_name="get_post",
                        description="Get post by ID",
                        parameters=[
                            {
                                "name": "post_id",
                                "type": "integer",
                                "required": True,
                                "location": "path",
                            }
                        ],
                    ),
                    EndpointConfig(
                        path="/posts",
                        method=HTTPMethod.POST,
                        mcp_type=MCPType.TOOL,
                        mcp_name="create_post",
                        description="Create post",
                        parameters=[
                            {
                                "name": "title",
                                "type": "string",
                                "required": True,
                                "location": "body",
                            },
                            {
                                "name": "body",
                                "type": "string",
                                "required": True,
                                "location": "body",
                            },
                            {
                                "name": "userId",
                                "type": "integer",
                                "required": True,
                                "location": "body",
                            },
                        ],
                    ),
                ],
            )
        ],
    )


@pytest.fixture
def config_manager(tmp_path, test_config):
    """Config manager fixture."""
    config_file = tmp_path / "config.yaml"
    # Write test config
    import yaml

    with open(config_file, "w") as f:
        yaml.dump(test_config.dict(), f)
    return ConfigManager(config_file)


@pytest.fixture
def gateway(config_manager):
    """Gateway fixture."""
    return MCPGateway(config_manager)


class TestMCPProtocol:
    """Test MCP protocol integration."""

    @pytest.mark.asyncio
    async def test_initialize_request(self, gateway):
        """Test MCP initialize request."""
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}},
            },
            "id": 1,
        }
        response = await gateway.jsonrpc_handler.handle_message(request)
        assert response is not None
        assert response.result["protocolVersion"] == "2024-11-05"
        assert "tools" in response.result["capabilities"]
        assert "resources" in response.result["capabilities"]

    @pytest.mark.asyncio
    async def test_tools_list_request(self, gateway):
        """Test MCP tools/list request."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1,
        }
        response = await gateway.jsonrpc_handler.handle_message(request)
        assert response is not None
        assert "tools" in response.result
        assert len(response.result["tools"]) > 0
        # Check that our test service tools are listed
        tool_names = [tool["name"] for tool in response.result["tools"]]
        assert "test_service.list_posts" in tool_names
        assert "test_service.get_post" in tool_names
        assert "test_service.create_post" in tool_names

    @pytest.mark.asyncio
    async def test_resources_list_request(self, gateway):
        """Test MCP resources/list request."""
        request = {
            "jsonrpc": "2.0",
            "method": "resources/list",
            "params": {},
            "id": 1,
        }
        response = await gateway.jsonrpc_handler.handle_message(request)
        assert response is not None
        assert "resources" in response.result

    @pytest.mark.asyncio
    async def test_tools_call_request(self, gateway):
        """Test MCP tools/call request."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "test_service.list_posts", "arguments": {}},
            "id": 1,
        }
        response = await gateway.jsonrpc_handler.handle_message(request)
        assert response is not None
        assert "result" in response

    @pytest.mark.asyncio
    async def test_tools_call_with_parameters(self, gateway):
        """Test MCP tools/call request with parameters."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "test_service.get_post",
                "arguments": {"post_id": 1},
            },
            "id": 1,
        }
        response = await gateway.jsonrpc_handler.handle_message(request)
        assert response is not None
        assert "result" in response

    @pytest.mark.asyncio
    async def test_tools_call_invalid_tool(self, gateway):
        """Test MCP tools/call request with invalid tool name."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "nonexistent.tool", "arguments": {}},
            "id": 1,
        }
        response = await gateway.jsonrpc_handler.handle_message(request)
        assert response is not None
        assert "error" in response
        assert response.error["code"] == -32601  # Method not found

    @pytest.mark.asyncio
    async def test_tools_call_missing_parameters(self, gateway):
        """Test MCP tools/call request with missing parameters."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "test_service.get_post",
                "arguments": {},  # Missing post_id
            },
            "id": 1,
        }
        response = await gateway.jsonrpc_handler.handle_message(request)
        assert response is not None
        assert "error" in response
        assert response.error["code"] == -32602  # Invalid params


class TestHTTPGateway:
    """Test HTTP gateway endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, gateway):
        """Test health check endpoint."""
        from fastapi.testclient import TestClient

        client = TestClient(gateway.app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "overall" in data
        assert "services" in data

    @pytest.mark.asyncio
    async def test_tools_endpoint(self, gateway):
        """Test tools listing endpoint."""
        from fastapi.testclient import TestClient

        client = TestClient(gateway.app)
        response = client.get("/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data

    @pytest.mark.asyncio
    async def test_resources_endpoint(self, gateway):
        """Test resources listing endpoint."""
        from fastapi.testclient import TestClient

        client = TestClient(gateway.app)
        response = client.get("/resources")
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self, gateway):
        """Test root endpoint."""
        from fastapi.testclient import TestClient

        client = TestClient(gateway.app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "MyUnla MCP Gateway"
        assert data["version"] == "1.0.0"
        assert "status" in data

    @pytest.mark.asyncio
    async def test_mcp_endpoint(self, gateway):
        """Test MCP JSON-RPC endpoint."""
        from fastapi.testclient import TestClient

        client = TestClient(gateway.app)
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
            "id": 1,
        }
        response = client.post("/mcp", json=request)
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert "result" in data
        assert data["id"] == 1


class TestConfigurationReload:
    """Test configuration reloading."""

    @pytest.mark.asyncio
    async def test_config_reload_callback(self, config_manager, tmp_path):
        """Test configuration reload callback."""
        gateway = MCPGateway(config_manager)
        # Modify config
        new_config = config_manager.get_config()
        new_config.services.append(
            ServiceConfig(
                name="new_service",
                description="New service",
                base_url="https://api.new.com",
            )
        )
        # Trigger reload
        gateway._on_config_reload(new_config)
        # Check that new service was loaded
        assert "new_service" in gateway.mapping_engine._service_cache


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_invalid_json_request(self, gateway):
        """Test handling of invalid JSON requests."""
        from fastapi.testclient import TestClient

        client = TestClient(gateway.app)
        # Send invalid JSON
        response = client.post("/mcp", data="invalid json")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_jsonrpc_parse_error(self, gateway):
        """Test handling of JSON-RPC parse errors."""
        from fastapi.testclient import TestClient

        client = TestClient(gateway.app)
        # Send malformed JSON-RPC
        request = {
            "jsonrpc": "1.0",
            "method": "test",
            "id": 1,
        }  # Invalid version
        response = client.post("/mcp", json=request)
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32700  # Parse error

    @pytest.mark.asyncio
    async def test_service_timeout(self, gateway):
        """Test handling of service timeouts."""
        with patch.object(
            gateway.transformation_pipeline._http_client, "request"
        ) as mock_request:
            # Mock timeout
            from httpx import TimeoutException

            mock_request.side_effect = TimeoutException("Request timeout")
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "test_service.list_posts", "arguments": {}},
                "id": 1,
            }
            response = await gateway.jsonrpc_handler.handle_message(request)
            assert response is not None
            assert "error" in response
            assert response.error["code"] == -32000  # Timeout error


class TestAuthenticationIntegration:
    """Test authentication integration."""

    @pytest.mark.asyncio
    async def test_api_key_authentication(self, config_manager, tmp_path):
        """Test API key authentication integration."""
        # Configure API key auth
        config = config_manager.get_config()
        config.services[0].auth = AuthenticationConfig(
            type=AuthType.API_KEY, api_key="test_key"
        )
        # Write updated config
        import yaml

        with open(config_manager.config_path, "w") as f:
            yaml.dump(config.dict(), f)
        # Reload config
        config_manager.load_config()
        gateway = MCPGateway(config_manager)
        gateway.auth_manager.config = config.services[0].auth
        from fastapi.testclient import TestClient

        client = TestClient(gateway.app)
        # Test without API key
        response = client.post(
            "/mcp", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        )
        assert response.status_code == 401
        # Test with valid API key
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers={"X-API-Key": "test_key"},
        )
        assert response.status_code == 200
