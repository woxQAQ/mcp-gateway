"""REST to MCP mapping engine."""

from typing import Any
from urllib.parse import urljoin

from myunla.models.config import (
    AuthenticationConfig,
    EndpointConfig,
    HTTPMethod,
    MCPType,
    ServiceConfig,
)
from myunla.utils.logger import get_logger

logger = get_logger(__name__)


class MappingEngine:
    """Engine for mapping REST API endpoints to MCP tools/resources."""

    def __init__(self) -> None:
        self._service_cache: dict[str, ServiceConfig] = {}
        self._endpoint_cache: dict[str, EndpointConfig] = {}

    def register_service(self, service: ServiceConfig) -> None:
        """Register a service and its endpoints."""
        self._service_cache[service.name] = service

        for endpoint in service.endpoints:
            cache_key = f"{service.name}.{endpoint.mcp_name}"
            self._endpoint_cache[cache_key] = endpoint

            logger.info(
                f"Registered endpoint: {service.name}.{endpoint.mcp_name} "
                f"({endpoint.method} {endpoint.path})"
            )

    def unregister_service(self, service_name: str) -> None:
        """Unregister a service and its endpoints."""
        if service_name in self._service_cache:
            del self._service_cache[service_name]

            # Remove endpoints from cache
            endpoints_to_remove = [
                key
                for key in self._endpoint_cache.keys()
                if key.startswith(f"{service_name}.")
            ]
            for key in endpoints_to_remove:
                del self._endpoint_cache[key]

            logger.info(f"Unregistered service: {service_name}")

    def get_service(self, service_name: str) -> ServiceConfig | None:
        """Get service configuration by name."""
        return self._service_cache.get(service_name)

    def get_endpoint(
        self, service_name: str, endpoint_name: str
    ) -> EndpointConfig | None:
        """Get endpoint configuration by service and endpoint name."""
        cache_key = f"{service_name}.{endpoint_name}"
        return self._endpoint_cache.get(cache_key)

    def list_tools(self) -> list[dict[str, Any]]:
        """List all available MCP tools."""
        tools = []

        for cache_key, endpoint in self._endpoint_cache.items():
            if endpoint.mcp_type == MCPType.TOOL:
                # service_name = cache_key.split(".")[0]
                tool_schema = self._create_tool_schema(endpoint)

                tools.append(
                    {
                        "name": endpoint.mcp_name,
                        "description": endpoint.description,
                        "inputSchema": tool_schema,
                    }
                )

        return tools

    def list_resources(self) -> list[dict[str, Any]]:
        """List all available MCP resources."""
        resources = []

        for cache_key, endpoint in self._endpoint_cache.items():
            if endpoint.mcp_type == MCPType.RESOURCE:
                service_name = cache_key.split(".")[0]

                resources.append(
                    {
                        "uri": f"mcp://{service_name}/{endpoint.mcp_name}",
                        "name": endpoint.mcp_name,
                        "description": endpoint.description,
                        "mimeType": "application/json",
                    }
                )

        return resources

    def build_request(
        self, service_name: str, endpoint_name: str, parameters: dict[str, Any]
    ) -> tuple[str, dict[str, str], dict[str, Any] | None]:
        """Build HTTP request from MCP parameters."""

        endpoint = self.get_endpoint(service_name, endpoint_name)
        if not endpoint:
            raise ValueError(
                f"Endpoint not found: {service_name}.{endpoint_name}"
            )

        service = self.get_service(service_name)
        if not service:
            raise ValueError(f"Service not found: {service_name}")

        # Build URL
        url = self._build_url(service.base_url, endpoint.path, parameters)

        # Build headers
        headers = self._build_headers(service, endpoint)

        # Build request body
        body = self._build_body(endpoint, parameters)

        return url, headers, body

    def transform_response(
        self, endpoint: EndpointConfig, response_data: Any
    ) -> Any:
        """Transform HTTP response to MCP format."""
        if not endpoint.response_mapping:
            return response_data

        try:
            # Apply response mapping if specified
            transformed = {}
            for mcp_field, rest_field in endpoint.response_mapping.items():
                if isinstance(rest_field, str):
                    # Simple field mapping
                    if rest_field in response_data:
                        transformed[mcp_field] = response_data[rest_field]
                elif isinstance(rest_field, dict):
                    # Complex transformation
                    if rest_field.get("path"):
                        value = response_data
                        for key in rest_field["path"].split("."):
                            if isinstance(value, dict) and key in value:
                                value = value[key]
                            else:
                                value = None
                                break

                        if value is not None:
                            if "transform" in rest_field:
                                value = self._apply_transform(
                                    value, rest_field["transform"]
                                )

                            transformed[mcp_field] = value

            return transformed

        except Exception as e:
            logger.error(f"Error transforming response: {e}")
            return response_data

    def _create_tool_schema(self, endpoint: EndpointConfig) -> dict[str, Any]:
        """Create JSON schema for MCP tool input."""
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": [],
        }

        for param in endpoint.parameters:
            prop_schema = {
                "type": param.type,
                "description": param.description or f"Parameter: {param.name}",
            }

            if param.default is not None:
                prop_schema["default"] = param.default

            schema["properties"][param.name] = prop_schema

            if param.required:
                schema["required"].append(param.name)

        return schema

    def _build_url(
        self, base_url: str, path_template: str, parameters: dict[str, Any]
    ) -> str:
        """Build URL from template and parameters."""

        # Extract path parameters
        path_params: dict[str, Any] = {}
        query_params: dict[str, Any] = {}

        for param in parameters:
            # This would be more efficient with pre-computed parameter locations
            path_params[param] = parameters[param]

        # Build path with path parameters
        path = path_template
        for param, value in path_params.items():
            path = path.replace(f"{{{param}}}", str(value))

        # Combine with base URL
        url = urljoin(base_url, path)

        # Add query parameters
        if query_params:
            from urllib.parse import urlencode

            query_string = urlencode(query_params)
            url = f"{url}?{query_string}"

        return url

    def _build_headers(
        self, service: ServiceConfig, endpoint: EndpointConfig
    ) -> dict[str, str]:
        """Build HTTP headers."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MyUnla-MCP-Gateway/1.0",
        }

        # Add service-level authentication
        if service.auth:
            auth_headers = self._build_auth_headers(service.auth)
            headers.update(auth_headers)

        # Add endpoint-level authentication (overrides service-level)
        if endpoint.auth:
            auth_headers = self._build_auth_headers(endpoint.auth)
            headers.update(auth_headers)

        return headers

    def _build_auth_headers(
        self, auth_config: AuthenticationConfig
    ) -> dict[str, str]:
        """Build authentication headers."""
        headers = {}

        if auth_config.type == "api_key" and auth_config.api_key:
            headers[auth_config.api_key_header] = auth_config.api_key

        elif auth_config.type == "bearer_token" and auth_config.bearer_token:
            headers["Authorization"] = f"Bearer {auth_config.bearer_token}"

        elif (
            auth_config.type == "basic_auth"
            and auth_config.basic_auth_username
            and auth_config.basic_auth_password
        ):
            import base64

            credentials = base64.b64encode(
                f"{auth_config.basic_auth_username}:{auth_config.basic_auth_password}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {credentials}"

        return headers

    def _build_body(
        self, endpoint: EndpointConfig, parameters: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Build request body from parameters."""

        if endpoint.method in [HTTPMethod.GET, HTTPMethod.DELETE]:
            return None

        # Extract body parameters
        body_params = {}

        for param_name, param_value in parameters.items():
            # For now, assume all parameters for POST/PUT go in body
            # This could be refined based on parameter location configuration
            body_params[param_name] = param_value

        return body_params if body_params else None

    def _apply_transform(
        self, value: Any, transform_config: dict[str, Any]
    ) -> Any:
        """Apply transformation to a value."""
        transform_type = transform_config.get("type")

        if transform_type == "stringify":
            return str(value)
        elif transform_type == "uppercase":
            return str(value).upper()
        elif transform_type == "lowercase":
            return str(value).lower()
        elif transform_type == "extract":
            if isinstance(value, dict) and "field" in transform_config:
                return value.get(transform_config["field"])
        elif transform_type == "map":
            if "mapping" in transform_config and isinstance(
                transform_config["mapping"], dict
            ):
                return transform_config["mapping"].get(str(value), value)

        return value
