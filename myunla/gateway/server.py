from typing import Optional

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse

from myunla.gateway.state import BackendProto, State
from myunla.utils.logger import get_logger

logger = get_logger(__name__)


class GatewayServer:
    def __init__(self, state: State):
        self.state = state
        self.app = FastAPI()
        self.setup_routes()

    def setup_routes(self):
        """设置路由"""

        # 处理所有未匹配的路由
        @self.app.api_route(
            "/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        )
        async def handle_root(request: Request, path: str):
            return await self.handle_root_request(request, path)

    async def handle_root_request(self, request: Request, path: str):
        """处理根路由请求 (对应Go代码中的handleRoot)"""
        # 获取路径并解析
        full_path = f"/{path}" if not path.startswith("/") else path
        parts = [p for p in full_path.strip("/").split("/") if p]

        if len(parts) < 2:
            logger.debug(
                "invalid path format",
                extra={
                    "path": full_path,
                    "remote_addr": (
                        request.client.host if request.client else "unknown"
                    ),
                },
            )
            return await self.send_protocol_error(
                "Invalid path", status.HTTP_400_BAD_REQUEST, "InvalidRequest"
            )

        endpoint = parts[-1]
        prefix = "/" + "/".join(parts[:-1])

        logger.debug(
            "routing request",
            extra={
                "path": full_path,
                "prefix": prefix,
                "endpoint": endpoint,
                "remote_addr": (
                    request.client.host if request.client else "unknown"
                ),
            },
        )

        # 检查认证配置
        auth_result = await self.check_auth(request, prefix)
        if auth_result:
            return auth_result

        # 动态设置CORS
        cors_result = await self.handle_cors(request, prefix)
        if cors_result:
            return cors_result

        # 验证前缀和获取协议类型
        proto_type = self.get_proto_type(prefix)
        if not proto_type:
            logger.warning(
                "invalid prefix",
                extra={
                    "prefix": prefix,
                    "remote_addr": (
                        request.client.host if request.client else "unknown"
                    ),
                },
            )
            return await self.send_protocol_error(
                "Invalid prefix", status.HTTP_404_NOT_FOUND, "InvalidRequest"
            )

        # 根据端点路由
        return await self.route_endpoint(request, prefix, endpoint)

    async def check_auth(
        self, request: Request, prefix: str
    ) -> Optional[JSONResponse]:
        """检查认证配置 (对应Go代码中的auth检查)"""
        # TODO: 实现OAuth2认证逻辑
        # auth = self.state.get_auth(prefix)
        # if auth and auth.mode == "oauth2":
        #     if not self.is_valid_access_token(request):
        #         return JSONResponse(
        #             status_code=status.HTTP_401_UNAUTHORIZED,
        #             content={
        #                 "error": "invalid_token",
        #                 "error_description": "Missing or invalid access token"
        #             },
        #             headers={"WWW-Authenticate": 'Bearer realm="OAuth", error="invalid_token"'}
        #         )
        return None

    async def handle_cors(
        self, request: Request, prefix: str
    ) -> Optional[Response]:
        """处理CORS (对应Go代码中的CORS处理)"""
        # TODO: 实现动态CORS设置
        # cors = self.state.get_cors(prefix)
        # if cors:
        #     logger.debug("applying CORS middleware", extra={"prefix": prefix})
        #     # 应用CORS逻辑
        return None

    def get_proto_type(self, prefix: str) -> Optional[str]:
        """获取协议类型 (对应Go代码中的GetProtoType)"""
        runtime = self.state.runtime.get(prefix)
        if not runtime:
            return None

        # 返回协议类型字符串
        return runtime.backend_proto.value

    async def route_endpoint(
        self, request: Request, prefix: str, endpoint: str
    ) -> Response:
        """根据端点路由到不同的处理器"""
        logger.debug(f"handling {endpoint} endpoint", extra={"prefix": prefix})

        match endpoint:
            case "sse":
                return await self.handle_sse(request, prefix)
            case "message":
                return await self.handle_message(request, prefix)
            case "mcp":
                return await self.handle_mcp(request, prefix)
            case _:
                logger.warning(
                    "invalid endpoint",
                    extra={
                        "endpoint": endpoint,
                        "prefix": prefix,
                        "remote_addr": (
                            request.client.host if request.client else "unknown"
                        ),
                    },
                )
                return await self.send_protocol_error(
                    "Invalid endpoint",
                    status.HTTP_404_NOT_FOUND,
                    "InvalidRequest",
                )

    async def handle_sse(self, request: Request, prefix: str) -> Response:
        """处理SSE端点"""
        # TODO: 实现SSE处理逻辑
        runtime = self.state.get_runtime(prefix)
        if runtime.backend_proto != BackendProto.SSE:
            return await self.send_protocol_error(
                "SSE not supported for this prefix",
                status.HTTP_400_BAD_REQUEST,
                "InvalidRequest",
            )

        return Response(
            "SSE endpoint - TODO: implement", media_type="text/plain"
        )

    async def handle_message(self, request: Request, prefix: str) -> Response:
        """处理消息端点"""
        # TODO: 实现消息处理逻辑
        runtime = self.state.get_runtime(prefix)

        return JSONResponse(
            content={
                "message": "Message endpoint",
                "prefix": prefix,
                "backend_proto": runtime.backend_proto.value,
            }
        )

    async def handle_mcp(self, request: Request, prefix: str) -> Response:
        """处理MCP端点"""
        # TODO: 实现MCP处理逻辑
        runtime = self.state.get_runtime(prefix)

        return JSONResponse(
            content={
                "message": "MCP endpoint",
                "prefix": prefix,
                "backend_proto": runtime.backend_proto.value,
                "tools": list(runtime.tools.keys()) if runtime.tools else [],
            }
        )

    async def send_protocol_error(
        self, message: str, status_code: int, error_code: str
    ) -> JSONResponse:
        """发送协议错误响应 (对应Go代码中的sendProtocolError)"""
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": error_code, "message": message}},
        )
