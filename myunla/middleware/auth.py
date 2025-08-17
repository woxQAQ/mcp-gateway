"""Authentication and authorization middleware for MCP Gateway."""

import base64
from typing import Any
from urllib.parse import parse_qs

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from myunla.models.config import AuthenticationConfig, AuthType
from myunla.utils.logger import get_logger

logger = get_logger(__name__)


class AuthenticationError(Exception):
    """Authentication error."""

    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class AuthorizationError(Exception):
    """Authorization error."""

    def __init__(self, message: str, code: str = "AUTHZ_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class AuthenticationManager:
    """Manages authentication for the MCP Gateway."""

    def __init__(self, config: AuthenticationConfig | None = None):
        self.config = config or AuthenticationConfig()
        self._api_keys: dict[str, dict[str, Any]] = {}
        self._bearer_tokens: dict[str, dict[str, Any]] = {}
        self._basic_auth: dict[tuple[str, str], dict[str, Any]] = {}

        # Initialize authentication handlers
        self._init_handlers()

    def _init_handlers(self):
        """Initialize authentication handlers based on configuration."""
        if self.config.type == AuthType.API_KEY:
            # Preload API keys from config
            if self.config.api_key:
                self._api_keys[self.config.api_key] = {"service": "default"}

        elif self.config.type == AuthType.BEARER_TOKEN:
            # Preload bearer tokens from config
            if self.config.bearer_token:
                self._bearer_tokens[self.config.bearer_token] = {
                    "service": "default"
                }

        elif self.config.type == AuthType.BASIC_AUTH:
            # Preload basic auth from config
            if (
                self.config.basic_auth_username
                and self.config.basic_auth_password
            ):
                self._basic_auth[
                    (
                        self.config.basic_auth_username,
                        self.config.basic_auth_password,
                    )
                ] = {"service": "default"}

    async def authenticate(self, request: Request) -> dict[str, Any]:
        """Authenticate the request based on configured method."""

        if self.config.type == AuthType.NONE:
            return {"user": "anonymous", "authenticated": False}

        try:
            if self.config.type == AuthType.API_KEY:
                return await self._authenticate_api_key(request)
            elif self.config.type == AuthType.BEARER_TOKEN:
                return await self._authenticate_bearer_token(request)
            elif self.config.type == AuthType.BASIC_AUTH:
                return await self._authenticate_basic_auth(request)
            elif self.config.type == AuthType.OAUTH2:
                return await self._authenticate_oauth2(request)
            else:
                raise AuthenticationError(
                    f"Unsupported authentication type: {self.config.type}"
                )

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise AuthenticationError("Authentication failed")

    async def _authenticate_api_key(self, request: Request) -> dict[str, Any]:
        """Authenticate using API key."""
        api_key_header = self.config.api_key_header or "X-API-Key"

        # Check headers
        api_key = request.headers.get(api_key_header)
        if api_key and api_key in self._api_keys:
            return {
                **self._api_keys[api_key],
                "authenticated": True,
                "method": "api_key",
            }

        # Check query parameters
        query_params = parse_qs(str(request.query_params))
        api_key = query_params.get("api_key", [None])[0]
        if api_key and api_key in self._api_keys:
            return {
                **self._api_keys[api_key],
                "authenticated": True,
                "method": "api_key",
            }

        raise AuthenticationError("Invalid API key")

    async def _authenticate_bearer_token(
        self, request: Request
    ) -> dict[str, Any]:
        """Authenticate using bearer token."""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthenticationError("Invalid bearer token format")

        token = auth_header[7:]  # Remove "Bearer " prefix
        if token in self._bearer_tokens:
            return {
                **self._bearer_tokens[token],
                "authenticated": True,
                "method": "bearer_token",
            }

        raise AuthenticationError("Invalid bearer token")

    async def _authenticate_basic_auth(
        self, request: Request
    ) -> dict[str, Any]:
        """Authenticate using basic auth."""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            raise AuthenticationError("Invalid basic auth format")

        try:
            # Decode base64 credentials
            encoded_credentials = auth_header[6:]  # Remove "Basic " prefix
            decoded_credentials = base64.b64decode(encoded_credentials).decode(
                "utf-8"
            )
            username, password = decoded_credentials.split(":", 1)

            if (username, password) in self._basic_auth:
                return {
                    **self._basic_auth[(username, password)],
                    "authenticated": True,
                    "method": "basic_auth",
                    "username": username,
                }

            raise AuthenticationError("Invalid basic auth credentials")

        except Exception as e:
            logger.error(f"Basic auth decode error: {e}")
            raise AuthenticationError("Invalid basic auth credentials")

    async def _authenticate_oauth2(self, request: Request) -> dict[str, Any]:
        """Authenticate using OAuth2."""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthenticationError("Invalid OAuth2 token format")

        token = auth_header[7:]  # Remove "Bearer " prefix

        # For now, just validate token format
        # In a real implementation, this would validate with OAuth2 provider
        if len(token) < 10:  # Basic validation
            raise AuthenticationError("Invalid OAuth2 token")

        return {
            "authenticated": True,
            "method": "oauth2",
            "token": token,
            "user": "oauth2_user",  # Would be extracted from token
        }

    def add_api_key(self, api_key: str, metadata: dict[str, Any] | None):
        """Add an API key."""
        self._api_keys[api_key] = metadata or {}

    def add_bearer_token(self, token: str, metadata: dict[str, Any] | None):
        """Add a bearer token."""
        self._bearer_tokens[token] = metadata or {}

    def add_basic_auth(
        self, username: str, password: str, metadata: dict[str, Any] | None
    ):
        """Add basic auth credentials."""
        self._basic_auth[(username, password)] = metadata or {}


class AuthorizationManager:
    """Manages authorization for the MCP Gateway."""

    def __init__(self):
        self._service_permissions: dict[str, dict[str, Any]] = {}
        self._user_permissions: dict[str, dict[str, Any]] = {}

    def authorize(
        self, auth_context: dict[str, Any], service_name: str, action: str
    ) -> bool:
        """Check if the authenticated user has permission to access the service."""

        # If not authenticated, only allow public access
        if not auth_context.get("authenticated", False):
            return self._is_public_service(service_name, action)

        # Check user-specific permissions
        user_id = auth_context.get("user") or auth_context.get("username")
        if user_id and user_id in self._user_permissions:
            user_perms = self._user_permissions[user_id]
            if self._check_permission(user_perms, service_name, action):
                return True

        # Check method-specific permissions
        method = auth_context.get("method")
        if method:
            method_perms = self._service_permissions.get(method, {})
            if self._check_permission(method_perms, service_name, action):
                return True

        # Default allow if no restrictions
        return True

    def _is_public_service(self, service_name: str, action: str) -> bool:
        """Check if a service/action is publicly accessible."""
        # For now, allow public access to health check and listing
        if service_name == "system" and action in ["health", "list"]:
            return True
        return False

    def _check_permission(
        self, permissions: dict[str, Any], service_name: str, action: str
    ) -> bool:
        """Check if permissions allow access to service/action."""

        # Check service-level permissions
        if service_name in permissions:
            service_perms = permissions[service_name]

            # If specific action is defined, check it
            if action in service_perms:
                return service_perms[action]

            # If no action specified, default to allow
            return True

        # Check wildcard permissions
        if "*" in permissions:
            wildcard_perms = permissions["*"]
            if action in wildcard_perms:
                return wildcard_perms[action]
            return True

        return False

    def set_service_permission(
        self, method: str, service_name: str, action: str, allowed: bool
    ):
        """Set permission for a service/action combination."""
        if method not in self._service_permissions:
            self._service_permissions[method] = {}

        if service_name not in self._service_permissions[method]:
            self._service_permissions[method][service_name] = {}

        self._service_permissions[method][service_name][action] = allowed

    def set_user_permission(
        self, user_id: str, service_name: str, action: str, allowed: bool
    ):
        """Set permission for a specific user."""
        if user_id not in self._user_permissions:
            self._user_permissions[user_id] = {}

        if service_name not in self._user_permissions[user_id]:
            self._user_permissions[user_id][service_name] = {}

        self._user_permissions[user_id][service_name][action] = allowed


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication and authorization middleware for FastAPI."""

    def __init__(
        self,
        app,
        auth_manager: AuthenticationManager,
        authz_manager: AuthorizationManager,
    ):
        super().__init__(app)
        self.auth_manager = auth_manager
        self.authz_manager = authz_manager

    async def dispatch(self, request: Request, call_next):
        """Process request through authentication and authorization."""

        # Skip auth for health check and public endpoints
        if self._is_public_endpoint(request):
            return await call_next(request)

        try:
            # Authenticate
            auth_context = await self.auth_manager.authenticate(request)

            # Add auth context to request state
            request.state.auth_context = auth_context

            # For MCP endpoint, check authorization
            if request.url.path == "/mcp":
                action = self._get_mcp_action(request)
                service_name = self._get_mcp_service(request)

                if not self.authz_manager.authorize(
                    auth_context, service_name, action
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied",
                    )

            # Continue with request
            response = await call_next(request)

            # Add auth headers to response
            if auth_context.get("authenticated"):
                response.headers["X-Authenticated"] = "true"
                response.headers["X-Auth-Method"] = auth_context.get(
                    "method", "unknown"
                )

            return response

        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=e.message,
                headers={
                    "WWW-Authenticate": self._get_www_authenticate_header()
                },
            )
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=e.message
            )

    def _is_public_endpoint(self, request: Request) -> bool:
        """Check if endpoint is public."""
        public_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        return any(request.url.path.startswith(path) for path in public_paths)

    def _get_mcp_action(self, request: Request) -> str:
        """Extract MCP action from request."""
        # This would parse the JSON-RPC request to determine the action
        # For now, return a default
        return "execute"

    def _get_mcp_service(self, request: Request) -> str:
        """Extract MCP service from request."""
        # This would parse the JSON-RPC request to determine the service
        # For now, return a default
        return "unknown"

    def _get_www_authenticate_header(self) -> str:
        """Get WWW-Authenticate header based on auth type."""
        if self.auth_manager.config.type == AuthType.BEARER_TOKEN:
            return 'Bearer realm="MCP Gateway"'
        elif self.auth_manager.config.type == AuthType.BASIC_AUTH:
            return 'Basic realm="MCP Gateway"'
        elif self.auth_manager.config.type == AuthType.API_KEY:
            return 'ApiKey realm="MCP Gateway"'
        return "MCP Gateway"
