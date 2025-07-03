from fastapi import FastAPI

from myunla.config import settings
from myunla.controllers import auth, mcp, openapi
from myunla.gateway import server as gateway_server

app = FastAPI(
    title="API Server",
    version="0.1.0",
    debug=settings.debug,
)

gateway = FastAPI(
    title="Gateway",
    version="0.1.0",
    debug=settings.debug,
)

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(mcp.router, prefix="/api/v1/mcp")
app.include_router(openapi.router, prefix="/api/v1/openapi")

gateway.include_router(gateway_server.router)
