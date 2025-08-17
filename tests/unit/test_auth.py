"""Unit tests for authentication middleware."""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException, Request, status

from myunla.middleware.auth import (
    AuthenticationError,
    AuthenticationManager,
    AuthMiddleware,
    AuthorizationManager,
)
from myunla.models.config import AuthenticationConfig, AuthType


class TestAuthenticationManager:
    """Test authentication manager."""

    def test_init_with_api_key(self):
        """Test initialization with API key auth."""
        config = AuthenticationConfig(type=AuthType.API_KEY, api_key="test_key")
        auth_manager = AuthenticationManager(config)
        assert "test_key" in auth_manager._api_keys

    def test_init_with_bearer_token(self):
        """Test initialization with bearer token auth."""
        config = AuthenticationConfig(
            type=AuthType.BEARER_TOKEN, bearer_token="test_token"
        )
        auth_manager = AuthenticationManager(config)
        assert "test_token" in auth_manager._bearer_tokens

    def test_init_with_basic_auth(self):
        """Test initialization with basic auth."""
        config = AuthenticationConfig(
            type=AuthType.BASIC_AUTH,
            basic_auth_username="testuser",
            basic_auth_password="testpass",
        )
        auth_manager = AuthenticationManager(config)
        assert ("testuser", "testpass") in auth_manager._basic_auth

    @pytest.mark.asyncio
    async def test_authenticate_api_key_header(self):
        """Test API key authentication via header."""
        config = AuthenticationConfig(type=AuthType.API_KEY, api_key="test_key")
        auth_manager = AuthenticationManager(config)
        request = Mock(spec=Request)
        request.headers = {"X-API-Key": "test_key"}
        request.query_params = {}
        auth_context = await auth_manager.authenticate(request)
        assert auth_context["authenticated"] is True
        assert auth_context["method"] == "api_key"

    @pytest.mark.asyncio
    async def test_authenticate_api_key_query(self):
        """Test API key authentication via query parameter."""
        config = AuthenticationConfig(type=AuthType.API_KEY, api_key="test_key")
        auth_manager = AuthenticationManager(config)
        request = Mock(spec=Request)
        request.headers = {}
        request.query_params = {"api_key": ["test_key"]}
        auth_context = await auth_manager.authenticate(request)
        assert auth_context["authenticated"] is True
        assert auth_context["method"] == "api_key"

    @pytest.mark.asyncio
    async def test_authenticate_bearer_token(self):
        """Test bearer token authentication."""
        config = AuthenticationConfig(
            type=AuthType.BEARER_TOKEN, bearer_token="test_token"
        )
        auth_manager = AuthenticationManager(config)
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer test_token"}
        auth_context = await auth_manager.authenticate(request)
        assert auth_context["authenticated"] is True
        assert auth_context["method"] == "bearer_token"

    @pytest.mark.asyncio
    async def test_authenticate_basic_auth(self):
        """Test basic authentication."""
        config = AuthenticationConfig(
            type=AuthType.BASIC_AUTH,
            basic_auth_username="testuser",
            basic_auth_password="testpass",
        )
        auth_manager = AuthenticationManager(config)
        request = Mock(spec=Request)
        request.headers = {
            "Authorization": "Basic dGVzdHVzZXI6dGVzdHBhc3M="
        }  # testuser:testpass
        auth_context = await auth_manager.authenticate(request)
        assert auth_context["authenticated"] is True
        assert auth_context["method"] == "basic_auth"
        assert auth_context["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_authenticate_none(self):
        """Test no authentication."""
        config = AuthenticationConfig(type=AuthType.NONE)
        auth_manager = AuthenticationManager(config)
        request = Mock(spec=Request)
        request.headers = {}
        auth_context = await auth_manager.authenticate(request)
        assert auth_context["authenticated"] is False
        assert auth_context["user"] == "anonymous"

    @pytest.mark.asyncio
    async def test_authenticate_invalid_api_key(self):
        """Test authentication with invalid API key."""
        config = AuthenticationConfig(type=AuthType.API_KEY, api_key="test_key")
        auth_manager = AuthenticationManager(config)
        request = Mock(spec=Request)
        request.headers = {"X-API-Key": "invalid_key"}
        request.query_params = {}
        with pytest.raises(AuthenticationError, match="Invalid API key"):
            await auth_manager.authenticate(request)

    @pytest.mark.asyncio
    async def test_authenticate_invalid_bearer_token(self):
        """Test authentication with invalid bearer token."""
        config = AuthenticationConfig(
            type=AuthType.BEARER_TOKEN, bearer_token="test_token"
        )
        auth_manager = AuthenticationManager(config)
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer invalid_token"}
        with pytest.raises(AuthenticationError, match="Invalid bearer token"):
            await auth_manager.authenticate(request)

    def test_add_api_key(self):
        """Test adding API key."""
        auth_manager = AuthenticationManager()
        auth_manager.add_api_key("new_key", {"service": "test"})
        assert "new_key" in auth_manager._api_keys
        assert auth_manager._api_keys["new_key"]["service"] == "test"

    def test_add_bearer_token(self):
        """Test adding bearer token."""
        auth_manager = AuthenticationManager()
        auth_manager.add_bearer_token("new_token", {"service": "test"})
        assert "new_token" in auth_manager._bearer_tokens
        assert auth_manager._bearer_tokens["new_token"]["service"] == "test"

    def test_add_basic_auth(self):
        """Test adding basic auth credentials."""
        auth_manager = AuthenticationManager()
        auth_manager.add_basic_auth("newuser", "newpass", {"service": "test"})
        assert ("newuser", "newpass") in auth_manager._basic_auth
        assert (
            auth_manager._basic_auth[("newuser", "newpass")]["service"]
            == "test"
        )


class TestAuthorizationManager:
    """Test authorization manager."""

    def test_authorize_public_service(self):
        """Test authorization for public service."""
        authz_manager = AuthorizationManager()
        auth_context = {"authenticated": False}
        result = authz_manager.authorize(auth_context, "system", "health")
        assert result is True

    def test_authorize_authenticated_user(self):
        """Test authorization for authenticated user."""
        authz_manager = AuthorizationManager()
        auth_context = {"authenticated": True, "method": "api_key"}
        result = authz_manager.authorize(
            auth_context, "test_service", "execute"
        )
        assert result is True

    def test_authorize_with_user_permissions(self):
        """Test authorization with user-specific permissions."""
        authz_manager = AuthorizationManager()
        authz_manager.set_user_permission(
            "testuser", "test_service", "execute", True
        )
        auth_context = {"authenticated": True, "user": "testuser"}
        result = authz_manager.authorize(
            auth_context, "test_service", "execute"
        )
        assert result is True

    def test_authorize_denied_permission(self):
        """Test authorization with denied permission."""
        authz_manager = AuthorizationManager()
        authz_manager.set_user_permission(
            "testuser", "test_service", "execute", False
        )
        auth_context = {"authenticated": True, "user": "testuser"}
        result = authz_manager.authorize(
            auth_context, "test_service", "execute"
        )
        assert result is False

    def test_set_service_permission(self):
        """Test setting service permission."""
        authz_manager = AuthorizationManager()
        authz_manager.set_service_permission(
            "api_key", "test_service", "execute", True
        )
        assert (
            authz_manager._service_permissions["api_key"]["test_service"][
                "execute"
            ]
            is True
        )

    def test_set_user_permission(self):
        """Test setting user permission."""
        authz_manager = AuthorizationManager()
        authz_manager.set_user_permission(
            "testuser", "test_service", "execute", True
        )
        assert (
            authz_manager._user_permissions["testuser"]["test_service"][
                "execute"
            ]
            is True
        )


class TestAuthMiddleware:
    """Test authentication middleware."""

    @pytest.mark.asyncio
    async def test_public_endpoint(self):
        """Test that public endpoints bypass authentication."""
        auth_manager = Mock(spec=AuthenticationManager)
        authz_manager = Mock(spec=AuthorizationManager)
        middleware = AuthMiddleware(None, auth_manager, authz_manager)
        request = Mock(spec=Request)
        request.url.path = "/health"
        call_next = AsyncMock()
        call_next.return_value = Mock()
        await middleware.dispatch(request, call_next)
        # Authentication should not be called for public endpoints
        auth_manager.authenticate.assert_not_called()
        authz_manager.authorize.assert_not_called()

    @pytest.mark.asyncio
    async def test_successful_authentication(self):
        """Test successful authentication flow."""
        auth_manager = Mock(spec=AuthenticationManager)
        authz_manager = Mock(spec=AuthorizationManager)
        auth_manager.authenticate.return_value = {
            "authenticated": True,
            "method": "api_key",
        }
        authz_manager.authorize.return_value = True
        middleware = AuthMiddleware(None, auth_manager, authz_manager)
        request = Mock(spec=Request)
        request.url.path = "/mcp"
        request.state = Mock()
        call_next = AsyncMock()
        call_next.return_value = Mock(headers={})
        response = await middleware.dispatch(request, call_next)
        # Authentication and authorization should be called
        auth_manager.authenticate.assert_called_once_with(request)
        authz_manager.authorize.assert_called_once()
        # Auth context should be added to request state
        assert hasattr(request.state, "auth_context")
        # Response should have auth headers
        assert response.headers["X-Authenticated"] == "true"
        assert response.headers["X-Auth-Method"] == "api_key"

    @pytest.mark.asyncio
    async def test_authentication_failure(self):
        """Test authentication failure."""
        auth_manager = Mock(spec=AuthenticationManager)
        authz_manager = Mock(spec=AuthorizationManager)
        auth_manager.authenticate.side_effect = AuthenticationError(
            "Invalid credentials"
        )
        middleware = AuthMiddleware(None, auth_manager, authz_manager)
        request = Mock(spec=Request)
        request.url.path = "/mcp"
        call_next = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, call_next)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"

    @pytest.mark.asyncio
    async def test_authorization_failure(self):
        """Test authorization failure."""
        auth_manager = Mock(spec=AuthenticationManager)
        authz_manager = Mock(spec=AuthorizationManager)
        auth_manager.authenticate.return_value = {
            "authenticated": True,
            "method": "api_key",
        }
        authz_manager.authorize.return_value = False
        middleware = AuthMiddleware(None, auth_manager, authz_manager)
        request = Mock(spec=Request)
        request.url.path = "/mcp"
        call_next = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, call_next)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Access denied"
