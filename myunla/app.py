from fastapi import FastAPI

from myunla.config import gateway_settings, settings
from myunla.controllers import auth, mcp, openapi
from myunla.gateway.server import GatewayServer
from myunla.gateway.state import Metrics, State

app = FastAPI(
    title="API Server",
    version="0.1.0",
    debug=settings.debug,
)

gateway_server = GatewayServer(
    State(
        mcps=[],
        runtime={},
        metrics=Metrics(),
    ),
    gateway_settings["session_config"],
)

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(mcp.router, prefix="/api/v1/mcp")
app.include_router(openapi.router, prefix="/api/v1/openapi")
