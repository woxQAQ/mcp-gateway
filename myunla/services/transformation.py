"""Request/response transformation pipeline."""

import json
from typing import Any

import httpx

from myunla.core.jsonrpc import JSONRPCError, MCPErrorCode
from myunla.models.config import MCPType
from myunla.services.mapping import MappingEngine
from myunla.utils.logger import get_logger

logger = get_logger(__name__)


class TransformationPipeline:
    """Pipeline for transforming MCP requests to HTTP requests and back."""

    def __init__(self, mapping_engine: MappingEngine):
        self.mapping_engine = mapping_engine
        self._http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(
                max_keepalive_connections=20, max_connections=100
            ),
        )

    async def process_tool_call(
        self, service_name: str, tool_name: str, parameters: dict[str, Any]
    ) -> Any:
        """Process a tool call through the transformation pipeline."""

        try:
            # Get endpoint configuration
            endpoint = self.mapping_engine.get_endpoint(service_name, tool_name)
            if not endpoint:
                raise JSONRPCError(
                    code=MCPErrorCode.METHOD_NOT_FOUND,
                    message=f"Tool not found: {service_name}.{tool_name}",
                )

            if endpoint.mcp_type != MCPType.TOOL:
                raise JSONRPCError(
                    code=MCPErrorCode.INVALID_REQUEST,
                    message=f"Endpoint {service_name}.{tool_name} is not a tool",
                ) from None

            logger.info(f"Processing tool call: {service_name}.{tool_name}")

            # Build HTTP request
            url, headers, body = self.mapping_engine.build_request(
                service_name, tool_name, parameters
            )

            # Execute HTTP request
            response_data = await self._execute_http_request(
                url, endpoint.method.value, headers, body
            )

            # Transform response
            result = self.mapping_engine.transform_response(
                endpoint, response_data
            )

            logger.info(f"Tool call completed: {service_name}.{tool_name}")
            return result

        except JSONRPCError as e:
            raise e
        except Exception as e:
            logger.error(
                f"Error processing tool call {service_name}.{tool_name}: {e}"
            )
            raise JSONRPCError(
                code=MCPErrorCode.INTERNAL_ERROR,
                message=f"Error processing tool call: {e!s}",
            ) from e

    async def process_resource_access(
        self, service_name: str, resource_name: str, parameters: dict[str, Any]
    ) -> Any:
        """Process a resource access through the transformation pipeline."""

        try:
            # Get endpoint configuration
            endpoint = self.mapping_engine.get_endpoint(
                service_name, resource_name
            )
            if not endpoint:
                raise JSONRPCError(
                    code=MCPErrorCode.METHOD_NOT_FOUND,
                    message=f"Resource not found: {service_name}.{resource_name}",
                )

            if endpoint.mcp_type != MCPType.RESOURCE:
                raise JSONRPCError(
                    code=MCPErrorCode.INVALID_REQUEST,
                    message=f"Endpoint {service_name}.{resource_name} is not a resource",
                ) from None

            logger.info(
                f"Processing resource access: {service_name}.{resource_name}"
            )

            # Build HTTP request
            url, headers, body = self.mapping_engine.build_request(
                service_name, resource_name, parameters
            )

            # Execute HTTP request
            response_data = await self._execute_http_request(
                url, endpoint.method.value, headers, body
            )

            # Transform response
            result = self.mapping_engine.transform_response(
                endpoint, response_data
            )

            logger.info(
                f"Resource access completed: {service_name}.{resource_name}"
            )
            return result

        except JSONRPCError as e:
            raise e
        except Exception as e:
            logger.error(
                f"Error processing resource access {service_name}.{resource_name}: {e}"
            )
            raise JSONRPCError(
                code=MCPErrorCode.INTERNAL_ERROR,
                message=f"Error processing resource access: {e!s}",
            ) from e

    async def _execute_http_request(
        self,
        url: str,
        method: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
    ) -> Any:
        """Execute HTTP request and return response data."""

        try:
            # Execute request
            response = await self._http_client.request(
                method, url, headers=headers, json=body, timeout=30.0
            )

            # Handle response
            if response.status_code >= 400:
                await self._handle_http_error(response)

            # Parse response
            try:
                if response.content:
                    return response.json()
                else:
                    return {"status": "success", "code": response.status_code}
            except json.JSONDecodeError:
                # Return raw content if not JSON
                return {
                    "content": response.text,
                    "content_type": response.headers.get("content-type"),
                }

        except httpx.TimeoutException as e:
            raise JSONRPCError(
                code=MCPErrorCode.TIMEOUT_ERROR, message="Request timeout"
            ) from e
        except httpx.NetworkError as e:
            raise JSONRPCError(
                code=MCPErrorCode.INTERNAL_ERROR,
                message=f"Network error: {e!s}",
            ) from e
        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            raise JSONRPCError(
                code=MCPErrorCode.INTERNAL_ERROR,
                message=f"HTTP request failed: {e!s}",
            ) from e

    async def _handle_http_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses."""

        error_data = None
        try:
            error_data = response.json()
        except json.JSONDecodeError:
            error_data = {"content": response.text}

        error_message = f"HTTP {response.status_code}"

        if isinstance(error_data, dict) and "message" in error_data:
            error_message = error_data["message"]
        elif isinstance(error_data, dict) and "error" in error_data:
            error_message = error_data["error"]

        # Map HTTP status codes to MCP error codes
        if response.status_code == 400:
            code = MCPErrorCode.INVALID_PARAMS
        elif response.status_code == 401:
            code = MCPErrorCode.AUTHENTICATION_ERROR
        elif response.status_code == 403:
            code = MCPErrorCode.AUTHORIZATION_ERROR
        elif response.status_code == 404:
            code = MCPErrorCode.RESOURCE_NOT_FOUND
        elif response.status_code == 429:
            code = MCPErrorCode.RATE_LIMIT_ERROR
        elif response.status_code >= 500:
            code = MCPErrorCode.INTERNAL_ERROR
        else:
            code = MCPErrorCode.INTERNAL_ERROR

        raise JSONRPCError(
            code=code, message=error_message, data=error_data
        ) from None

    async def validate_request(
        self, service_name: str, endpoint_name: str, parameters: dict[str, Any]
    ) -> bool:
        """Validate request parameters against endpoint schema."""

        endpoint = self.mapping_engine.get_endpoint(service_name, endpoint_name)
        if not endpoint:
            return False

        # Validate required parameters
        for param in endpoint.parameters:
            if param.required and param.name not in parameters:
                return False

        # Validate parameter types
        for param_name, param_value in parameters.items():
            param_config = next(
                (p for p in endpoint.parameters if p.name == param_name), None
            )

            if param_config:
                try:
                    expected_type = param_config.type
                    if expected_type == "string":
                        if not isinstance(param_value, str):
                            return False
                    elif expected_type == "integer":
                        if not isinstance(param_value, int):
                            return False
                    elif expected_type == "number":
                        if not isinstance(param_value, (int, float)):
                            return False
                    elif expected_type == "boolean":
                        if not isinstance(param_value, bool):
                            return False
                    elif expected_type == "array":
                        if not isinstance(param_value, list):
                            return False
                    elif expected_type == "object":
                        if not isinstance(param_value, dict):
                            return False
                except Exception:
                    return False

        return True

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on all configured services."""

        health_status: dict[str, Any] = {"overall": "healthy", "services": {}}

        services = list(self.mapping_engine._service_cache.keys())
        unhealthy_count = 0

        for service_name in services:
            service_healthy = await self._check_service_health(service_name)
            health_status["services"][service_name] = (
                "healthy" if service_healthy else "unhealthy"
            )

            if not service_healthy:
                unhealthy_count += 1

        if unhealthy_count > 0:
            health_status["overall"] = "degraded"
            if unhealthy_count == len(services):
                health_status["overall"] = "unhealthy"

        return health_status

    async def _check_service_health(self, service_name: str) -> bool:
        """Check health of a specific service."""

        try:
            service = self.mapping_engine.get_service(service_name)
            if not service:
                return False

            # Try to make a simple GET request to the base URL
            response = await self._http_client.get(
                service.base_url,
                timeout=10.0,
                headers={"User-Agent": "MyUnla-MCP-Gateway/1.0"},
            )

            return response.status_code < 500

        except Exception as e:
            logger.warning(
                f"Health check failed for service {service_name}: {e}"
            )
            return False

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        await self._http_client.aclose()
        logger.info("Transformation pipeline closed")
