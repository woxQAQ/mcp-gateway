from fastapi import FastAPI

from myunla.controllers import auth, mcp

app = FastAPI(
    title="API Server",
    version="0.1.0",
)

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(mcp.router, prefix="/api/v1/mcp")
