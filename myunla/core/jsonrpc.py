"""JSON-RPC 2.0 message handling for MCP protocol."""

import json
import uuid
from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import BaseModel, validator

from myunla.utils.logger import get_logger

logger = get_logger(__name__)


class JSONRPCVersion(str, Enum):
    """JSON-RPC version."""

    V2_0 = "2.0"


class JSONRPCError(Exception):
    """JSON-RPC error object."""

    def __init__(
        self, code: int, message: str, data: Any | None = None
    ) -> None:
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class JSONRPCRequest(BaseModel):
    """JSON-RPC request object."""

    jsonrpc: JSONRPCVersion = JSONRPCVersion.V2_0
    method: str
    params: dict[str, Any] | None = None
    id: str | int | None = None

    @validator("id")
    def validate_id(cls, v: Any) -> Any:
        """Validate request ID."""
        if v is not None and not isinstance(v, (str, int)):
            raise ValueError("id must be string or integer")
        return v


class JSONRPCResponse(BaseModel):
    """JSON-RPC response object."""

    jsonrpc: JSONRPCVersion = JSONRPCVersion.V2_0
    result: Any | None = None
    error: dict[str, Any] | None = None
    id: str | int | None = None

    @validator("id")
    def validate_id(cls, v: Any) -> Any:
        """Validate response ID."""
        if v is not None and not isinstance(v, (str, int)):
            raise ValueError("id must be string or integer")
        return v

    @validator("result", "error")
    def validate_result_error(cls, v: Any, values: dict[str, Any]) -> Any:
        """Ensure only one of result or error is present."""
        if "result" in values and "error" in values:
            if values["result"] is not None and v is not None:
                raise ValueError("only one of result or error can be present")
        return v


class JSONRPCNotification(BaseModel):
    """JSON-RPC notification object."""

    jsonrpc: JSONRPCVersion = JSONRPCVersion.V2_0
    method: str
    params: dict[str, Any] | None = None


class MCPErrorCode(int, Enum):
    """MCP-specific error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    TIMEOUT_ERROR = -32604
    AUTHENTICATION_ERROR = -32605
    AUTHORIZATION_ERROR = -32606
    RATE_LIMIT_ERROR = -32607
    RESOURCE_NOT_FOUND = -32608
    VALIDATION_ERROR = -32609


class JSONRPCMessageHandler:
    """Handler for JSON-RPC 2.0 messages."""

    def __init__(self) -> None:
        self._methods: dict[str, Callable[..., Any]] = {}
        self._request_id_counter = 0

    def register_method(
        self, method_name: str, handler: Callable[..., Any]
    ) -> None:
        """Register a method handler."""
        self._methods[method_name] = handler
        logger.info(f"Registered method: {method_name}")

    def unregister_method(self, method_name: str) -> None:
        """Unregister a method handler."""
        if method_name in self._methods:
            del self._methods[method_name]
            logger.info(f"Unregistered method: {method_name}")

    def parse_message(
        self, message: str | bytes | dict[str, Any]
    ) -> JSONRPCRequest | JSONRPCNotification:
        """Parse JSON-RPC message from string or dict."""
        try:
            if isinstance(message, (str, bytes)):
                data = json.loads(message)
            else:
                data = message

            # Check if it's a notification (no id)
            if "id" not in data:
                return JSONRPCNotification(**data)

            return JSONRPCRequest(**data)

        except json.JSONDecodeError as e:
            error = JSONRPCError(
                code=MCPErrorCode.PARSE_ERROR,
                message="Parse error: Invalid JSON",
            )
            raise error from e
        except Exception as e:
            error = JSONRPCError(
                code=MCPErrorCode.INVALID_REQUEST,
                message=f"Invalid request: {e!s}",
            )
            raise error from e

    def create_response(
        self,
        result: Any = None,
        error: JSONRPCError | None = None,
        request_id: str | int | None = None,
    ) -> JSONRPCResponse:
        """Create JSON-RPC response."""
        error_dict = None
        if error:
            error_dict = {"code": error.code, "message": error.message}
            if error.data is not None:
                error_dict["data"] = error.data
        return JSONRPCResponse(result=result, error=error_dict, id=request_id)

    def create_error_response(
        self,
        code: int,
        message: str,
        data: Any = None,
        request_id: str | int | None = None,
    ) -> JSONRPCResponse:
        """Create JSON-RPC error response."""
        error_dict = {"code": code, "message": message}
        if data is not None:
            error_dict["data"] = data
        return JSONRPCResponse(result=None, error=error_dict, id=request_id)

    def create_notification(
        self, method: str, params: dict[str, Any] | None = None
    ) -> JSONRPCNotification:
        """Create JSON-RPC notification."""
        return JSONRPCNotification(method=method, params=params)

    async def handle_message(
        self, message: str | bytes | dict[str, Any]
    ) -> JSONRPCResponse:
        """Handle incoming JSON-RPC message."""
        try:
            request = self.parse_message(message)

            if isinstance(request, JSONRPCNotification):
                # Handle notification (no response expected)
                await self._handle_notification(request)
                return self.create_response()  # Return empty response

            # Handle request
            return await self._handle_request(request)

        except JSONRPCError as e:
            return self.create_response(
                error=e, request_id=getattr(request, "id", None)
            )
        except Exception as e:
            logger.error(f"Unexpected error handling message: {e}")
            return self.create_error_response(
                code=MCPErrorCode.INTERNAL_ERROR,
                message="Internal server error",
                data=str(e),
            )

    async def _handle_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Handle JSON-RPC request."""
        method_name = request.method

        if method_name not in self._methods:
            return self.create_error_response(
                code=MCPErrorCode.METHOD_NOT_FOUND,
                message=f"Method not found: {method_name}",
                request_id=request.id,
            )

        try:
            handler = self._methods[method_name]
            result = await handler(request.params or {})

            return self.create_response(result=result, request_id=request.id)

        except JSONRPCError as e:
            response = self.create_response(error=e, request_id=request.id)
            return response
        except Exception as e:
            logger.error(f"Error executing method {method_name}: {e}")
            return self.create_error_response(
                code=MCPErrorCode.INTERNAL_ERROR,
                message=f"Error executing method: {method_name}",
                data=str(e),
                request_id=request.id,
            )

    async def _handle_notification(
        self, notification: JSONRPCNotification
    ) -> None:
        """Handle JSON-RPC notification."""
        method_name = notification.method

        if method_name in self._methods:
            try:
                handler = self._methods[method_name]
                if callable(handler):
                    await handler(notification.params or {})
            except Exception as e:
                logger.error(f"Error handling notification {method_name}: {e}")
        else:
            logger.warning(
                f"Received notification for unknown method: {method_name}"
            )

    def generate_request_id(self) -> str:
        """Generate a unique request ID."""
        return str(uuid.uuid4())

    def serialize_response(self, response: JSONRPCResponse) -> str:
        """Serialize JSON-RPC response to JSON string."""
        return response.json(exclude_none=True)

    def serialize_notification(self, notification: JSONRPCNotification) -> str:
        """Serialize JSON-RPC notification to JSON string."""
        return notification.json(exclude_none=True)

    def validate_params(
        self, params: dict[str, Any], schema: dict[str, Any]
    ) -> bool:
        """Validate parameters against JSON schema."""
        try:
            # Basic validation - in production, use a proper JSON schema validator
            required_fields = schema.get("required", [])
            properties = schema.get("properties", {})

            # Check required fields
            for field in required_fields:
                if field not in params:
                    return False

            # Check field types
            for field, value in params.items():
                if field in properties:
                    expected_type = properties[field].get("type")
                    if expected_type and expected_type in (
                        "str",
                        "int",
                        "float",
                        "bool",
                        "list",
                        "dict",
                    ):
                        expected_type_map = {
                            "str": str,
                            "int": int,
                            "float": float,
                            "bool": bool,
                            "list": list,
                            "dict": dict,
                        }
                        if not isinstance(
                            value, expected_type_map[expected_type]
                        ):
                            return False

            return True

        except Exception as e:
            logger.error(f"Error validating parameters: {e}")
            return False
