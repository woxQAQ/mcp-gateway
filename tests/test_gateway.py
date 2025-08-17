"""Unit tests for MCP Gateway."""

import asyncio
from unittest.mock import Mock, patch

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
def sample_config():
    """Sample configuration for testing."""
    return GatewayConfig(
        version="1.0",
        services=[
            ServiceConfig(
                name="test_service",
                description="Test service",
                base_url="https://api.example.com",
                auth=AuthenticationConfig(
                    type=AuthType.API_KEY, api_key="test_key"
                ),
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
        ],
    )


@pytest.fixture
def config_manager(tmp_path, sample_config):
    """Config manager fixture."""
    config_file = tmp_path / "config.yaml"
    # Write sample config
    import yaml

    with open(config_file, "w") as f:
        yaml.dump(sample_config.dict(), f)
    return ConfigManager(config_file)


@pytest.fixture
def gateway(config_manager):
    """Gateway fixture."""
    return MCPGateway(config_manager)


class TestConfigManager:
    """Test configuration management."""

    def test_load_config(self, tmp_path):
        """Test loading configuration from file."""
        config_data = {
            "version": "1.0",
            "services": [
                {
                    "name": "test",
                    "description": "Test service",
                    "base_url": "https://api.example.com",
                }
            ],
        }
        config_file = tmp_path / "config.yaml"
        import yaml

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        manager = ConfigManager(config_file)
        config = manager.get_config()
        assert config.version == "1.0"
        assert len(config.services) == 1
        assert config.services[0].name == "test"

    def test_config_validation(self, tmp_path):
        """Test configuration validation."""
        # Invalid config - missing required fields
        config_data = {
            "version": "1.0",
            "services": [
                {
                    "name": "test"
                    # Missing base_url
                }
            ],
        }
        config_file = tmp_path / "config.yaml"
        import yaml

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        manager = ConfigManager(config_file)
        assert not manager.validate_config()


class TestMappingEngine:
    """Test mapping engine functionality."""

    def test_register_service(self, gateway):
        """Test service registration."""
        service = ServiceConfig(
            name="test_service",
            description="Test service",
            base_url="https://api.example.com",
        )
        gateway.mapping_engine.register_service(service)
        assert "test_service" in gateway.mapping_engine._service_cache
        assert gateway.mapping_engine.get_service("test_service") == service

    def test_get_endpoint(self, gateway):
        """Test endpoint retrieval."""
        service = ServiceConfig(
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
        gateway.mapping_engine.register_service(service)
        endpoint = gateway.mapping_engine.get_endpoint(
            "test_service", "list_users"
        )
        assert endpoint is not None
        assert endpoint.mcp_name == "list_users"

    def test_build_request(self, gateway):
        """Test request building."""
        service = ServiceConfig(
            name="test_service",
            description="Test service",
            base_url="https://api.example.com",
            endpoints=[
                EndpointConfig(
                    path="/users/{user_id}",
                    method=HTTPMethod.GET,
                    mcp_type=MCPType.TOOL,
                    mcp_name="get_user",
                    description="Get user",
                )
            ],
        )
        gateway.mapping_engine.register_service(service)
        url, headers, body = gateway.mapping_engine.build_request(
            "test_service", "get_user", {"user_id": "123"}
        )
        assert url == "https://api.example.com/users/123"
        assert headers == {}
        assert body is None


class TestTransformationPipeline:
    """Test transformation pipeline."""

    @pytest.mark.asyncio
    async def test_validate_request(self, gateway):
        """Test request validation."""
        service = ServiceConfig(
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
                    parameters=[
                        {"name": "limit", "type": "integer", "required": True}
                    ],
                )
            ],
        )
        gateway.mapping_engine.register_service(service)
        # Valid request
        valid = await gateway.transformation_pipeline.validate_request(
            "test_service", "list_users", {"limit": 10}
        )
        assert valid is True
        # Invalid request - missing required parameter
        valid = await gateway.transformation_pipeline.validate_request(
            "test_service", "list_users", {}
        )
        assert valid is False

    @pytest.mark.asyncio
    async def test_health_check(self, gateway):
        """Test health check functionality."""
        with patch.object(
            gateway.transformation_pipeline._http_client, "get"
        ) as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            health = await gateway.transformation_pipeline.health_check()
            assert health["overall"] == "healthy"
            assert "services" in health


class TestAuthentication:
    """Test authentication functionality."""

    def test_api_key_auth(self):
        """Test API key authentication."""
        from myunla.middleware.auth import (
            AuthenticationConfig,
            AuthenticationManager,
        )

        config = AuthenticationConfig(type=AuthType.API_KEY, api_key="test_key")
        auth_manager = AuthenticationManager(config)
        # Mock request with valid API key
        request = Mock()
        request.headers = {"X-API-Key": "test_key"}
        auth_context = asyncio.run(auth_manager.authenticate(request))
        assert auth_context["authenticated"] is True
        assert auth_context["method"] == "api_key"

    def test_bearer_token_auth(self):
        """Test bearer token authentication."""
        from myunla.middleware.auth import (
            AuthenticationConfig,
            AuthenticationManager,
        )

        config = AuthenticationConfig(
            type=AuthType.BEARER_TOKEN, bearer_token="test_token"
        )
        auth_manager = AuthenticationManager(config)
        # Mock request with valid bearer token
        request = Mock()
        request.headers = {"Authorization": "Bearer test_token"}
        auth_context = asyncio.run(auth_manager.authenticate(request))
        assert auth_context["authenticated"] is True
        assert auth_context["method"] == "bearer_token"

    def test_basic_auth(self):
        """Test basic authentication."""
        from myunla.middleware.auth import (
            AuthenticationConfig,
            AuthenticationManager,
        )

        config = AuthenticationConfig(
            type=AuthType.BASIC_AUTH,
            basic_auth_username="testuser",
            basic_auth_password="testpass",
        )
        auth_manager = AuthenticationManager(config)
        # Mock request with valid basic auth
        request = Mock()
        request.headers = {
            "Authorization": "Basic dGVzdHVzZXI6dGVzdHBhc3M="
        }  # testuser:testpass
        auth_context = asyncio.run(auth_manager.authenticate(request))
        assert auth_context["authenticated"] is True
        assert auth_context["method"] == "basic_auth"


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_check(self):
        """Test rate limit checking."""
        from myunla.middleware.rate_limit import RateLimitConfig, RateLimiter

        config = RateLimitConfig(requests_per_minute=5)
        limiter = RateLimiter(config)
        # Should allow requests within limit
        for i in range(5):
            allowed = asyncio.run(limiter.check_rate_limit("test_key", 60, 5))
            assert allowed is True
        # Should block request exceeding limit
        allowed = asyncio.run(limiter.check_rate_limit("test_key", 60, 5))
        assert allowed is False

    def test_rate_limit_cleanup(self):
        """Test rate limit cleanup."""
        from myunla.middleware.rate_limit import RateLimitConfig, RateLimiter

        config = RateLimitConfig()
        limiter = RateLimiter(config)
        # Add some requests
        asyncio.run(limiter.check_rate_limit("test_key", 60, 5))
        # Check that requests are tracked
        assert len(limiter._requests["test_key"]) == 1
        # Cleanup should remove old requests
        limiter.cleanup()


class TestJSONRPCHandler:
    """Test JSON-RPC message handling."""

    def test_parse_valid_request(self):
        """Test parsing valid JSON-RPC request."""
        from myunla.core.jsonrpc import JSONRPCMessageHandler

        handler = JSONRPCMessageHandler()
        request_data = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1,
        }
        request = handler._parse_request(request_data)
        assert request.method == "tools/list"
        assert request.id == 1

    def test_parse_invalid_request(self):
        """Test parsing invalid JSON-RPC request."""
        from myunla.core.jsonrpc import JSONRPCError, JSONRPCMessageHandler

        handler = JSONRPCMessageHandler()
        # Missing required fields
        request_data = {"jsonrpc": "2.0"}
        with pytest.raises(JSONRPCError):
            handler._parse_request(request_data)

    def test_method_registration(self):
        """Test method registration and calling."""
        from myunla.core.jsonrpc import JSONRPCMessageHandler

        handler = JSONRPCMessageHandler()

        async def test_method(params):
            return {"result": "test"}

        handler.register_method("test.method", test_method)
        # Should call registered method
        request_data = {
            "jsonrpc": "2.0",
            "method": "test.method",
            "params": {},
            "id": 1,
        }
        response = asyncio.run(handler.handle_message(request_data))
        assert response is not None
        assert response.result == {"result": "test"}
