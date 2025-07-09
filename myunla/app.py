from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from myunla.config import gateway_settings, settings
from myunla.controllers import auth, mcp, openapi
from myunla.gateway.server import GatewayServer
from myunla.gateway.state import Metrics, State
from myunla.utils import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="API Server",
    version="0.1.0",
    debug=settings.debug,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],  # Vite开发服务器
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

gateway_server = GatewayServer(
    State(
        mcps=[],
        runtime={},
        metrics=Metrics(),
    ),
    gateway_settings["session_config"],
)


# 全局异常处理器 - 限制错误信息长度
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器，限制错误信息长度"""
    error_message = str(exc)

    # 限制错误信息长度为200字符
    if len(error_message) > 200:
        error_message = error_message[:200] + "..."

    # 记录完整错误信息到日志
    logger.error(f"全局异常: {exc.__class__.__name__}: {exc!s}")

    # 返回简化的错误信息
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {error_message}"},
    )


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(
    request: Request, exc: StarletteHTTPException
):
    """自定义HTTP异常处理器，限制错误信息长度"""
    error_message = str(exc.detail)

    # 限制错误信息长度为200字符
    if len(error_message) > 200:
        error_message = error_message[:200] + "..."

    # 记录错误信息到日志
    logger.warning(f"HTTP异常 {exc.status_code}: {exc.detail!s}")

    # 返回简化的错误信息
    return JSONResponse(
        status_code=exc.status_code, content={"detail": error_message}
    )


app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(mcp.router, prefix="/api/v1/mcp")
app.include_router(openapi.router, prefix="/api/v1/openapi")
