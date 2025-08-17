"""Core MCP Gateway implementation."""

import json
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from myunla.config.manager import ConfigManager
from myunla.core.jsonrpc import (
    JSONRPCError,
    JSONRPCMessageHandler,
    MCPErrorCode,
)
from myunla.middleware.auth import (
    AuthenticationManager,
    AuthMiddleware,
    AuthorizationManager,
)
from myunla.middleware.rate_limit import AbuseDetector, RateLimitMiddleware
from myunla.observability.logging import get_logger, setup_logging
from myunla.services.mapping import MappingEngine
from myunla.services.transformation import TransformationPipeline

logger = get_logger(__name__)


class MCPGateway:
    """Main MCP Gateway implementation."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.mapping_engine = MappingEngine()
        self.transformation_pipeline = TransformationPipeline(
            self.mapping_engine
        )
        self.jsonrpc_handler = JSONRPCMessageHandler()

        # Initialize middleware managers
        self.auth_manager = AuthenticationManager()
        self.authz_manager = AuthorizationManager()
        self.abuse_detector = AbuseDetector()
        desc = "A secure, observable gateway for RESTful API to MCP conversion"

        self.app = FastAPI(
            title="MyUnla MCP Gateway",
            description=desc,
            version="1.0.0",
        )

        self._setup_middleware()
        self._setup_routes()
        self._setup_mcp_methods()
        self._load_services()

        # Register config reload callback
        self.config_manager.add_reload_callback(self._on_config_reload)

    def _setup_middleware(self):
        """Setup FastAPI middleware."""
        config = self.config_manager.get_config()

        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Rate limiting middleware
        self.app.add_middleware(
            RateLimitMiddleware, config=config.rate_limiting
        )

        # Authentication middleware
        self.app.add_middleware(
            AuthMiddleware,
            auth_manager=self.auth_manager,
            authz_manager=self.authz_manager,
        )

        # TODO: Add OpenTelemetry instrumentation

    def _setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return await self.transformation_pipeline.health_check()

        @self.app.get("/tools")
        async def list_tools():
            """List available MCP tools."""
            return {"tools": self.mapping_engine.list_tools()}

        @self.app.get("/resources")
        async def list_resources():
            """List available MCP resources."""
            return {"resources": self.mapping_engine.list_resources()}

        @self.app.post("/mcp")
        async def handle_mcp_request(request: Request):
            """Handle MCP JSON-RPC requests."""
            try:
                # Parse request body
                body = await request.body()

                # Handle JSON-RPC message
                response = await self.jsonrpc_handler.handle_message(body)

                if response is None:
                    # Notification (no response)
                    return JSONResponse(status_code=204)

                return JSONResponse(
                    content=json.loads(response.json(exclude_none=True)),
                    status_code=200,
                )

            except JSONRPCError as e:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": e.code,
                            "message": e.message,
                            "data": e.data,
                        },
                        "id": None,
                    },
                    status_code=400,
                )
            except Exception as e:
                logger.error(f"Error handling MCP request: {e}")
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": MCPErrorCode.INTERNAL_ERROR,
                            "message": "Internal server error",
                        },
                        "id": None,
                    },
                    status_code=500,
                )

        @self.app.get("/")
        async def root():
            """Root endpoint with gateway information."""
            return {
                "name": "MyUnla MCP Gateway",
                "version": "1.0.0",
                "status": "running",
                "services": len(self.config_manager.get_config().services),
                "tools": len(self.mapping_engine.list_tools()),
                "resources": len(self.mapping_engine.list_resources()),
            }

    def _setup_mcp_methods(self):
        """Setup MCP protocol method handlers."""

        async def handle_tools_list(params: dict[str, Any]) -> dict[str, Any]:
            """Handle tools/list method."""
            return {"tools": self.mapping_engine.list_tools()}

        async def handle_tools_call(params: dict[str, Any]) -> Any:
            """Handle tools/call method."""
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if not tool_name:
                raise JSONRPCError(
                    code=MCPErrorCode.INVALID_PARAMS,
                    message="Tool name is required",
                )

            # Parse tool name (format: service.tool)
            if "." not in tool_name:
                raise JSONRPCError(
                    code=MCPErrorCode.INVALID_PARAMS,
                    message="Tool name must be in format: service.tool",
                )

            service_name, endpoint_name = tool_name.split(".", 1)

            # Validate request
            if not await self.transformation_pipeline.validate_request(
                service_name, endpoint_name, arguments
            ):
                raise JSONRPCError(
                    code=MCPErrorCode.INVALID_PARAMS,
                    message="Invalid parameters for tool",
                )

            # Process tool call
            return await self.transformation_pipeline.process_tool_call(
                service_name, endpoint_name, arguments
            )

        async def handle_resources_list(
            params: dict[str, Any],
        ) -> dict[str, Any]:
            """Handle resources/list method."""
            return {"resources": self.mapping_engine.list_resources()}

        async def handle_resources_read(params: dict[str, Any]) -> Any:
            """Handle resources/read method."""
            resource_uri = params.get("uri")

            if not resource_uri:
                raise JSONRPCError(
                    code=MCPErrorCode.INVALID_PARAMS,
                    message="Resource URI is required",
                )

            # Parse resource URI (format: mcp://service/resource)
            if not resource_uri.startswith("mcp://"):
                raise JSONRPCError(
                    code=MCPErrorCode.INVALID_PARAMS,
                    message="Invalid resource URI format",
                )

            try:
                # Parse URI
                uri_parts = resource_uri[6:].split("/")  # Remove "mcp://"
                service_name = uri_parts[0]
                resource_name = uri_parts[1] if len(uri_parts) > 1 else ""

                if not service_name or not resource_name:
                    raise JSONRPCError(
                        code=MCPErrorCode.INVALID_PARAMS,
                        message="Invalid resource URI format",
                    )

                # Process resource access
                return (
                    await self.transformation_pipeline.process_resource_access(
                        service_name, resource_name, {}
                    )
                )

            except Exception as e:
                raise JSONRPCError(
                    code=MCPErrorCode.INVALID_PARAMS,
                    message=f"Invalid resource URI: {e!s}",
                )

        async def handle_initialize(params: dict[str, Any]) -> dict[str, Any]:
            """Handle initialize method."""
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "logging": {},
                    "prompts": {},
                },
                "serverInfo": {
                    "name": "MyUnla MCP Gateway",
                    "version": "1.0.0",
                },
            }

        # Register method handlers
        self.jsonrpc_handler.register_method("tools/list", handle_tools_list)
        self.jsonrpc_handler.register_method("tools/call", handle_tools_call)
        self.jsonrpc_handler.register_method(
            "resources/list", handle_resources_list
        )
        self.jsonrpc_handler.register_method(
            "resources/read", handle_resources_read
        )
        self.jsonrpc_handler.register_method("initialize", handle_initialize)

    def _load_services(self):
        """Load services from configuration."""
        config = self.config_manager.get_config()

        for service in config.services:
            self.mapping_engine.register_service(service)

        logger.info(f"Loaded {len(config.services)} services")

    def _on_config_reload(self, config):
        """Handle configuration reload."""
        logger.info("Reloading services configuration")

        # Clear existing services
        for service_name in list(self.mapping_engine._service_cache.keys()):
            self.mapping_engine.unregister_service(service_name)

        # Reload services
        for service in config.services:
            self.mapping_engine.register_service(service)

        # Update authentication configuration
        if config.services:
            self.auth_manager.config = config.services[0].auth

        logger.info(f"Reloaded {len(config.services)} services")

    async def run(self):
        """Run the MCP Gateway."""
        config = self.config_manager.get_config().server

        # Setup logging
        observability_config = self.config_manager.get_config().observability
        setup_logging(level="INFO", format_type="text")

        # Setup tracing if enabled
        if observability_config.tracing_enabled:
            try:
                from myunla.observability.tracing import setup_tracing

                setup_tracing(
                    service_name=observability_config.service_name,
                    jaeger_endpoint=observability_config.jaeger_endpoint,
                    otlp_endpoint=observability_config.otlp_endpoint,
                )
            except ImportError as e:
                logger.warning(f"Failed to setup tracing: {e}")

        logger.info(f"Starting MCP Gateway on {config.host}:{config.port}")

        # Run with uvicorn
        uvicorn_config = uvicorn.Config(
            app=self.app,
            host=config.host,
            port=config.port,
            workers=config.workers,
            reload=config.reload,
            access_log=config.access_log,
            log_level="info",
        )

        server = uvicorn.Server(uvicorn_config)
        await server.serve()

    async def stop(self):
        """Stop the MCP Gateway."""
        logger.info("Stopping MCP Gateway")
        await self.transformation_pipeline.close()
        self.config_manager.stop()
