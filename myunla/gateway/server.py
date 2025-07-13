import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from mcp import (
    InitializeResult,
    JSONRPCRequest,
    ListToolsResult,
    ServerCapabilities,
    Tool,
    ToolsCapability,
)
from mcp.types import (
    LATEST_PROTOCOL_VERSION,
    CallToolRequestParams,
    CallToolResult,
    Implementation,
    InitializeRequestParams,
    TextContent,
)

from myunla.config.session_config import SessionConfig
from myunla.gateway.session import (
    Meta,
    RequestInfo,
)
from myunla.gateway.session.session import Connection, create_store
from myunla.gateway.state import State
from myunla.gateway.state_loader import state_loader
from myunla.templates.context import RequestWrapper
from myunla.utils import get_logger

logger = get_logger(__name__)

# MCP协议常量
MCP_METHOD_INITIALIZE = "initialize"
MCP_METHOD_INITIALIZED = "notifications/initialized"
MCP_METHOD_PING = "ping"
MCP_METHOD_TOOLS_LIST = "tools/list"
MCP_METHOD_TOOLS_CALL = "tools/call"


class GatewayServer:
    def __init__(
        self, state: State, session_config: Optional[SessionConfig] = None
    ):
        self.state = state
        self.app = FastAPI()
        self.last_update_time: Optional[datetime] = None
        self._initialized = False

        # 初始化会话存储
        if session_config is None:
            session_config = SessionConfig()  # 使用默认配置
        self.sessions = create_store(session_config)
        self.initialize_state()

        self.setup_routes()

    def initialize_state(self) -> None:
        """从数据库初始化网关状态"""
        try:
            logger.info("开始初始化网关服务器状态...")

            # 从数据库加载并构建新状态
            new_state = state_loader.initialize_gateway_state(self.state)

            # 更新状态
            self.state = new_state
            self.last_update_time = datetime.now()
            self._initialized = True

            logger.info("网关服务器状态初始化完成")
            logger.info(
                f"Gateway initialized with prefixes: {list(self.state.runtime.keys())}"
            )

        except Exception as e:
            logger.error(f"网关服务器状态初始化失败: {e}")
            # 使用初始状态继续运行
            self._initialized = True

    def is_initialized(self) -> bool:
        """检查网关状态是否已初始化"""
        return self._initialized

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

        logger.warning(
            f"routing request - path: {full_path}, prefix: {prefix}, endpoint: {endpoint}, "
            f"available_prefixes: {list(self.state.runtime.keys())}"
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
            logger.debug(
                "runtime not found for prefix",
                extra={
                    "prefix": prefix,
                    "available_prefixes": list(self.state.runtime.keys()),
                },
            )
            return None

        # 返回协议类型字符串
        return runtime.backend_proto.value

    async def route_endpoint(
        self, request: Request, prefix: str, endpoint: str
    ) -> Response:
        """根据端点路由到不同的处理器"""
        logger.debug(f"handling {endpoint} endpoint", extra={"prefix": prefix})

        if endpoint == "sse":
            return await self.handle_sse(request, prefix)
        elif endpoint == "message":
            return await self.handle_message(request, prefix)
        elif endpoint == "mcp":
            return await self.handle_mcp(request, prefix)
        else:
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
        # runtime = self.state.get_runtime(prefix)
        # if runtime.backend_proto != BackendProto.SSE:
        #     return await self.send_protocol_error(
        #         "SSE not supported for this prefix",
        #         status.HTTP_400_BAD_REQUEST,
        #         "InvalidRequest",
        #     )

        # 设置SSE响应头
        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        }

        # 获取请求信息
        request_info = RequestInfo(
            headers=dict(request.headers.items()),
            queries=dict(request.query_params.items()),
            cookies=dict(request.cookies.items()),
        )

        # 创建会话ID和元数据
        session_id = str(uuid.uuid4())
        meta = Meta(
            id=session_id,
            created_at=datetime.now(),
            prefix=prefix,
            type="sse",
            request=request_info,
            extra=None,
        )

        logger.info(
            "建立SSE连接",
            extra={
                "session_id": session_id,
                "prefix": prefix,
                "remote_addr": (
                    request.client.host if request.client else "unknown"
                ),
                "user_agent": request.headers.get("user-agent", ""),
            },
        )

        try:
            # 注册会话
            conn = await self.sessions.register(meta)

            logger.debug(
                "SSE会话注册成功",
                extra={"session_id": session_id, "prefix": prefix},
            )

            # 获取SSE前缀配置
            sse_prefix = self.state.get_sse_prefix(prefix)

            # 构建endpoint URL
            endpoint_url = f"{prefix}/message?sessionId={session_id}"
            if sse_prefix:
                endpoint_url = f"{sse_prefix}/{endpoint_url.lstrip('/')}"

            logger.debug(
                "发送初始endpoint事件",
                extra={
                    "session_id": session_id,
                    "endpoint_url": endpoint_url,
                },
            )

            async def event_generator():
                try:
                    # 发送初始endpoint事件
                    yield f"event: endpoint\ndata: {endpoint_url}\n\n"

                    logger.info(
                        "SSE连接就绪",
                        extra={
                            "session_id": session_id,
                            "prefix": prefix,
                            "remote_addr": (
                                request.client.host
                                if request.client
                                else "unknown"
                            ),
                        },
                    )

                    # 主事件循环
                    while True:
                        try:
                            # 等待事件或检测连接断开
                            event_queue = conn.event_queue()

                            # 使用超时来定期检查连接状态
                            try:
                                event = await asyncio.wait_for(
                                    event_queue.get(),
                                    timeout=25.0,  # 减少到25秒
                                )
                            except TimeoutError:
                                # 发送心跳事件
                                logger.debug(
                                    "发送SSE心跳包",
                                    extra={"session_id": session_id},
                                )
                                yield "event: heartbeat\ndata: ping\n\n"
                                continue

                            if event is None:
                                logger.warning(
                                    "收到空事件",
                                    extra={"session_id": session_id},
                                )
                                continue

                            logger.debug(
                                "发送事件到SSE客户端",
                                extra={
                                    "session_id": session_id,
                                    "event_type": event.event,
                                    "data_size": len(event.data),
                                },
                            )

                            if event.event == "message":
                                yield f"event: message\ndata: {event.data.decode('utf-8')}\n\n"
                            else:
                                yield f"event: {event.event}\ndata: {event.data.decode('utf-8')}\n\n"

                        except Exception as e:
                            logger.error(
                                "处理SSE事件时发生错误",
                                extra={
                                    "error": str(e),
                                    "session_id": session_id,
                                },
                            )
                            break

                except asyncio.CancelledError:
                    logger.info(
                        "SSE客户端断开连接",
                        extra={"session_id": session_id},
                    )
                    raise
                except Exception as e:
                    logger.error(
                        "SSE连接发生错误",
                        extra={
                            "error": str(e),
                            "session_id": session_id,
                        },
                    )
                    raise
                finally:
                    # 清理会话
                    try:
                        await self.sessions.unregister(session_id)
                        logger.info(
                            "SSE会话已清理",
                            extra={"session_id": session_id},
                        )
                    except Exception as e:
                        logger.error(
                            "清理SSE会话时发生错误",
                            extra={
                                "error": str(e),
                                "session_id": session_id,
                            },
                        )

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers=headers,
            )

        except Exception as e:
            logger.error(
                "建立SSE连接失败",
                extra={
                    "error": str(e),
                    "session_id": session_id,
                    "prefix": prefix,
                    "remote_addr": (
                        request.client.host if request.client else "unknown"
                    ),
                },
            )
            return await self.send_protocol_error(
                "Failed to create SSE connection",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "InternalError",
            )

    async def handle_message(self, request: Request, prefix: str) -> Response:
        """处理消息端点 (对应Go代码中的handleMessage和handlePostMessage)"""
        logger.debug(
            "收到消息请求",
            extra={
                "method": request.method,
                "path": str(request.url.path),
                "remote_addr": (
                    request.client.host if request.client else "unknown"
                ),
            },
        )

        # 获取sessionId查询参数
        session_id = request.query_params.get("sessionId")
        if not session_id:
            logger.warning(
                "缺少sessionId参数",
                extra={
                    "path": str(request.url.path),
                    "remote_addr": (
                        request.client.host if request.client else "unknown"
                    ),
                },
            )
            return await self.send_protocol_error_with_id(
                "Missing sessionId parameter",
                status.HTTP_400_BAD_REQUEST,
                "InvalidRequest",
            )

        # 从会话存储中获取连接
        try:
            conn = await self.sessions.get(session_id)
            if conn is None:
                logger.error(
                    "会话未找到",
                    extra={
                        "session_id": session_id,
                        "remote_addr": (
                            request.client.host if request.client else "unknown"
                        ),
                    },
                )
                return JSONResponse(
                    content={"error": "Session not found"},
                    status_code=status.HTTP_404_NOT_FOUND,
                )
        except Exception as e:
            logger.error(
                "获取会话失败",
                extra={
                    "error": str(e),
                    "session_id": session_id,
                    "remote_addr": (
                        request.client.host if request.client else "unknown"
                    ),
                },
            )
            return JSONResponse(
                content={"error": "Session not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        logger.debug(
            "处理会话消息",
            extra={
                "session_id": session_id,
                "prefix": conn.meta().prefix,
            },
        )

        return await self.handle_post_message(request, conn)

    async def handle_post_message(
        self, request: Request, conn: Connection
    ) -> Response:
        """处理POST消息 (对应Go代码中的handlePostMessage)"""
        if conn is None:
            logger.error(
                "空的SSE连接",
                extra={
                    "remote_addr": (
                        request.client.host if request.client else "unknown"
                    ),
                },
            )
            return JSONResponse(
                content={"error": "SSE connection not established"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 验证Content-Type头
        content_type = request.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            logger.warning(
                "无效的内容类型",
                extra={
                    "content_type": content_type,
                    "session_id": conn.meta().id,
                    "remote_addr": (
                        request.client.host if request.client else "unknown"
                    ),
                },
            )
            return JSONResponse(
                content={
                    "error": "Unsupported Media Type: Content-Type must be application/json"
                },
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
            )

        # TODO: 支持身份验证

        # 解析JSON-RPC消息
        try:
            body = await request.body()
            req_data = json.loads(body)

            # 验证JSON-RPC格式
            if not isinstance(req_data, dict) or "method" not in req_data:
                raise ValueError("Invalid JSON-RPC format")

            # 创建JSON-RPC请求对象
            request_id = req_data.get("id", "")  # 使用空字符串作为默认值
            jsonrpc_req = JSONRPCRequest(
                jsonrpc=req_data.get("jsonrpc", "2.0"),
                method=req_data["method"],
                params=req_data.get("params"),
                id=request_id,
            )

        except json.JSONDecodeError as e:
            logger.error(
                "解析JSON-RPC请求失败",
                extra={
                    "error": str(e),
                    "session_id": conn.meta().id,
                    "remote_addr": (
                        request.client.host if request.client else "unknown"
                    ),
                },
            )
            return JSONResponse(
                content={"error": "Invalid message"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(
                "处理JSON-RPC请求失败",
                extra={
                    "error": str(e),
                    "session_id": conn.meta().id,
                    "remote_addr": (
                        request.client.host if request.client else "unknown"
                    ),
                },
            )
            return JSONResponse(
                content={"error": "Invalid message"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        logger.debug(
            "收到JSON-RPC请求",
            extra={
                "method": jsonrpc_req.method,
                "id": jsonrpc_req.id,
                "session_id": conn.meta().id,
            },
        )

        # 处理不同的方法
        return await self.handle_jsonrpc_method(request, conn, jsonrpc_req)

    async def handle_jsonrpc_method(
        self, request: Request, conn: Connection, jsonrpc_req: JSONRPCRequest
    ) -> Response:
        """处理具体的JSON-RPC方法"""
        try:
            if jsonrpc_req.method == MCP_METHOD_INITIALIZED:
                return await self.send_accepted_response()

            elif jsonrpc_req.method == MCP_METHOD_INITIALIZE:
                # 解析初始化参数
                try:
                    from mcp.types import ClientCapabilities

                    params_data = jsonrpc_req.params or {}

                    # 处理capabilities参数
                    capabilities_data = params_data.get("capabilities")
                    capabilities = (
                        ClientCapabilities()
                        if capabilities_data is None
                        else ClientCapabilities(**capabilities_data)
                    )

                    # 处理clientInfo参数
                    client_info_data = params_data.get("clientInfo")
                    client_info = (
                        Implementation(name="Unknown", version="0.0.0")
                        if client_info_data is None
                        else Implementation(**client_info_data)
                    )

                    params = InitializeRequestParams(
                        protocolVersion=params_data.get(
                            "protocolVersion", LATEST_PROTOCOL_VERSION
                        ),
                        capabilities=capabilities,
                        clientInfo=client_info,
                    )
                except Exception as e:
                    return await self.send_protocol_error_with_id(
                        "Invalid initialize parameters",
                        status.HTTP_400_BAD_REQUEST,
                        "InvalidParams",
                        jsonrpc_req.id,
                    )

                # 构建初始化结果
                result = InitializeResult(
                    protocolVersion=LATEST_PROTOCOL_VERSION,
                    serverInfo=Implementation(
                        name="MyUnla Gateway",
                        version="0.1.0",
                    ),
                    capabilities=ServerCapabilities(
                        tools=ToolsCapability(listChanged=True),
                    ),
                )

                return await self.send_success_response(
                    conn, jsonrpc_req, result, True
                )

            elif jsonrpc_req.method == MCP_METHOD_PING:
                # 处理ping请求，返回空响应
                return await self.send_success_response(
                    conn, jsonrpc_req, {}, True
                )

            elif jsonrpc_req.method == MCP_METHOD_TOOLS_LIST:
                proto_type = self.state.get_proto_type(conn.meta().prefix)
                if not proto_type:
                    return await self.send_protocol_error_with_id(
                        "Server configuration not found",
                        status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "InternalError",
                        jsonrpc_req.id,
                    )

                tools = []
                try:
                    if proto_type == "http":
                        tools = await self.fetch_http_tool_list(conn)
                    elif proto_type in ["stdio", "sse", "streamable"]:
                        transport = self.state.get_transport(conn.meta().prefix)
                        if transport is None:
                            return await self.send_protocol_error_with_id(
                                "Failed to fetch tools",
                                status.HTTP_500_INTERNAL_SERVER_ERROR,
                                "InternalError",
                                jsonrpc_req.id,
                            )
                        tools = await transport.fetch_tools()
                    else:
                        return await self.send_protocol_error_with_id(
                            "Unsupported protocol type",
                            status.HTTP_400_BAD_REQUEST,
                            "InvalidParams",
                            jsonrpc_req.id,
                        )
                except Exception as e:
                    logger.error(f"获取工具列表失败: {e}")
                    return await self.send_protocol_error_with_id(
                        "Failed to fetch tools",
                        status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "InternalError",
                        jsonrpc_req.id,
                    )

                # 转换工具格式
                tool_schemas = []
                for tool in tools:
                    if hasattr(tool, 'name') and hasattr(tool, 'description'):
                        tool_schema = Tool(
                            name=tool.name,
                            description=tool.description,
                            inputSchema=getattr(tool, 'inputSchema', {}),
                        )
                        tool_schemas.append(tool_schema)

                result = ListToolsResult(tools=tool_schemas)
                return await self.send_success_response(
                    conn, jsonrpc_req, result, True
                )

            elif jsonrpc_req.method == MCP_METHOD_TOOLS_CALL:
                proto_type = self.state.get_proto_type(conn.meta().prefix)
                if not proto_type:
                    return await self.send_protocol_error_with_id(
                        "Server configuration not found",
                        status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "InternalError",
                        jsonrpc_req.id,
                    )

                # 解析工具调用参数
                try:
                    params_data = jsonrpc_req.params or {}
                    params = CallToolRequestParams(
                        name=params_data.get("name", ""),
                        arguments=params_data.get("arguments", {}),
                    )
                    if not params.name:
                        raise ValueError("Missing tool name")
                except Exception as e:
                    return await self.send_protocol_error_with_id(
                        "Invalid tool call parameters",
                        status.HTTP_400_BAD_REQUEST,
                        "InvalidParams",
                        jsonrpc_req.id,
                    )

                # 执行工具调用
                try:
                    result = None
                    if proto_type == "http":
                        result = await self.call_http_tool(
                            request, jsonrpc_req, conn, params
                        )
                    elif proto_type in ["stdio", "sse", "streamable"]:
                        transport = self.state.get_transport(conn.meta().prefix)
                        if transport is None:
                            return await self.send_protocol_error_with_id(
                                "Server configuration not found",
                                status.HTTP_404_NOT_FOUND,
                                "MethodNotFound",
                                jsonrpc_req.id,
                            )

                        # 合并请求信息
                        request_wrapper = await self.merge_request_info(
                            conn.meta().request, request
                        )

                        mcp_params = CallToolRequestParams(
                            name=params.name, arguments=params.arguments
                        )

                        result = await transport.call_tools(
                            mcp_params, request_wrapper
                        )
                    else:
                        return await self.send_protocol_error_with_id(
                            "Unsupported protocol type",
                            status.HTTP_400_BAD_REQUEST,
                            "InvalidParams",
                            jsonrpc_req.id,
                        )

                    return await self.send_success_response(
                        conn, jsonrpc_req, result, True
                    )

                except Exception as e:
                    logger.error(f"工具执行失败: {e}")
                    return await self.send_tool_execution_error(
                        conn, jsonrpc_req, e, True
                    )

            else:
                return await self.send_protocol_error_with_id(
                    "Unknown method",
                    status.HTTP_404_NOT_FOUND,
                    "MethodNotFound",
                    jsonrpc_req.id,
                )

        except Exception as e:
            logger.error(f"处理JSON-RPC方法失败: {e}")
            return await self.send_protocol_error_with_id(
                "Internal server error",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "InternalError",
                jsonrpc_req.id,
            )

    async def send_accepted_response(self) -> Response:
        """发送接受响应"""
        return JSONResponse(
            content={"status": "accepted"}, status_code=status.HTTP_202_ACCEPTED
        )

    async def send_success_response(
        self,
        conn,
        jsonrpc_req: JSONRPCRequest,
        result: Any,
        send_via_sse: bool = False,
    ) -> Response:
        """发送成功响应"""
        # 处理结果序列化
        if hasattr(result, 'model_dump'):
            result_data = result.model_dump()
        elif hasattr(result, 'dict'):
            result_data = result.dict()
        else:
            result_data = result

        response_data = {
            "jsonrpc": "2.0",
            "id": jsonrpc_req.id,
            "result": result_data,
        }

        if send_via_sse and conn:
            # 通过SSE发送响应
            try:
                from myunla.gateway.session import Message

                message = Message(
                    event="jsonrpc_response",
                    data=json.dumps(response_data).encode('utf-8'),
                )
                await conn.send(message)
            except Exception as e:
                logger.error(f"通过SSE发送响应失败: {e}")

        return JSONResponse(
            content=response_data, status_code=status.HTTP_200_OK
        )

    async def send_tool_execution_error(
        self,
        conn,
        jsonrpc_req: JSONRPCRequest,
        error: Exception,
        send_via_sse: bool = False,
    ) -> Response:
        """发送工具执行错误响应"""
        error_response = {
            "jsonrpc": "2.0",
            "id": jsonrpc_req.id,
            "error": {
                "code": "ToolExecutionError",
                "message": f"Tool execution failed: {error!s}",
            },
        }

        if send_via_sse and conn:
            try:
                from myunla.gateway.session import Message

                message = Message(
                    event="jsonrpc_error",
                    data=json.dumps(error_response).encode('utf-8'),
                )
                await conn.send(message)
            except Exception as e:
                logger.error(f"通过SSE发送错误响应失败: {e}")

        return JSONResponse(
            content=error_response,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    async def fetch_http_tool_list(self, conn: Connection) -> list:
        """获取HTTP工具列表 (对应Go代码中的fetchHTTPToolList)"""
        logger.debug(
            "fetching HTTP tool list",
            extra={
                "session_id": conn.meta().id,
                "prefix": conn.meta().prefix,
            },
        )

        # 从state中获取指定prefix的工具schemas
        runtime = self.state.get_runtime(conn.meta().prefix)
        tools = runtime.tools_schema
        if len(tools) == 0:
            logger.warning(
                "no tools found for prefix",
                extra={
                    "prefix": conn.meta().prefix,
                    "session_id": conn.meta().id,
                },
            )
            tools = []  # 如果没有找到prefix则返回空列表

        logger.debug(
            "fetched tool list",
            extra={
                "prefix": conn.meta().prefix,
                "session_id": conn.meta().id,
                "tool_count": len(tools),
            },
        )

        return tools

    async def call_http_tool(
        self,
        request: Request,
        jsonrpc_req: JSONRPCRequest,
        conn: Connection,
        params: CallToolRequestParams,
    ) -> CallToolResult:
        """调用HTTP工具 (对应Go代码中的callHTTPTool)"""
        # 记录工具调用信息（info级别）
        logger.info(
            "invoking HTTP tool",
            extra={
                "tool": params.name,
                "session_id": conn.meta().id,
                "remote_addr": (
                    request.client.host if request.client else "unknown"
                ),
            },
        )

        # 从预计算的映射中查找工具
        runtime = self.state.get_runtime(conn.meta().prefix)
        tool = runtime.tools.get(params.name)
        if tool is None:
            logger.warning(
                "tool not found",
                extra={
                    "tool": params.name,
                    "session_id": conn.meta().id,
                    "remote_addr": (
                        request.client.host if request.client else "unknown"
                    ),
                },
            )
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Tool {params.name} not found",
                    )
                ],
                isError=True,
            )

        # 解析参数
        args = params.arguments or {}

        # 记录工具参数（debug级别）
        logger.debug(
            "tool arguments",
            extra={
                "tool": params.name,
                "session_id": conn.meta().id,
                "arguments": json.dumps(args),
            },
        )

        # 获取服务器配置
        if not runtime.http_server:
            logger.error(
                "server configuration not found",
                extra={
                    "tool": params.name,
                    "prefix": conn.meta().prefix,
                    "session_id": conn.meta().id,
                },
            )
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Server configuration not found",
                    )
                ],
                isError=True,
            )

        # 执行工具
        try:
            result = await self.execute_http_tool(
                conn, tool, args, request, runtime.http_server
            )
            if result is None:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Tool execution failed",
                        )
                    ],
                    isError=True,
                )

            logger.info(
                "tool invocation completed successfully",
                extra={
                    "tool": params.name,
                    "session_id": conn.meta().id,
                },
            )

            return result

        except Exception as e:
            logger.error(
                "tool execution failed",
                extra={
                    "tool": params.name,
                    "session_id": conn.meta().id,
                    "error": str(e),
                },
            )
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Tool execution failed: {e!s}",
                    )
                ],
                isError=True,
            )

    async def execute_http_tool(
        self,
        conn: Connection,
        tool,
        args: dict,
        request: Request,
        server_config,
    ) -> Optional[CallToolResult]:
        """执行HTTP工具 (对应Go代码中的executeHTTPTool)"""
        try:
            # 填充默认参数值
            self.fill_default_args(tool, args)

            # 规范化JSON字符串值
            await self.normalize_json_string_values(args)

            # 记录工具执行信息（info级别）
            logger.info(
                "executing HTTP tool",
                extra={
                    "tool": tool.name,
                    "method": getattr(tool, 'method', 'GET'),
                    "session_id": conn.meta().id,
                    "remote_addr": (
                        request.client.host if request.client else "unknown"
                    ),
                },
            )

            # 准备模板上下文
            tmpl_ctx = await self.prepare_template_context(
                conn.meta().request, args, request, server_config
            )

            # 准备HTTP请求
            http_request = await self.prepare_request(tool, tmpl_ctx)

            # 记录请求详情（debug级别）
            logger.debug(
                "tool request details",
                extra={
                    "tool": tool.name,
                    "url": str(http_request.url),
                    "method": http_request.method,
                    "headers": dict(http_request.headers),
                },
            )

            # 处理参数
            await self.process_arguments(http_request, tool, args)

            # 创建HTTP客户端
            http_client = await self.create_http_client(tool)

            logger.debug(
                "sending HTTP request",
                extra={
                    "tool": tool.name,
                    "url": str(http_request.url),
                    "session_id": conn.meta().id,
                },
            )

            # 执行请求
            async with http_client as client:
                response = await client.send(http_request)

            # 读取响应体
            response_body = response.content

            # 记录响应状态
            logger.debug(
                "received HTTP response",
                extra={
                    "tool": tool.name,
                    "session_id": conn.meta().id,
                    "response_body": response_body.decode(
                        'utf-8', errors='ignore'
                    ),
                    "status": response.status_code,
                },
            )

            # 处理响应
            call_tool_result = await self.handle_tool_response(
                response, tool, tmpl_ctx
            )

            logger.info(
                "tool execution completed successfully",
                extra={
                    "tool": tool.name,
                    "session_id": conn.meta().id,
                    "status": response.status_code,
                },
            )

            return call_tool_result

        except Exception as e:
            logger.error(
                "failed to execute HTTP tool",
                extra={
                    "tool": tool.name,
                    "session_id": conn.meta().id,
                    "error": str(e),
                },
            )
            raise

    def fill_default_args(self, tool, args: dict) -> None:
        """填充默认参数值 (对应Go代码中的fillDefaultArgs)"""
        # TODO: 实现默认参数填充逻辑
        pass

    async def normalize_json_string_values(self, args: dict) -> None:
        """规范化JSON字符串值 (对应Go代码中的template.NormalizeJSONStringValues)"""
        # TODO: 实现JSON字符串值规范化
        pass

    async def prepare_template_context(
        self,
        session_request: RequestInfo,
        args: dict,
        request: Request,
        server_config,
    ):
        """准备模板上下文 (对应Go代码中的template.PrepareTemplateContext)"""
        # TODO: 实现模板上下文准备
        return {
            "args": args,
            "request": session_request,
            "current_request": request,
            "server_config": server_config,
        }

    async def prepare_request(self, tool, tmpl_ctx):
        """准备HTTP请求 (对应Go代码中的prepareRequest)"""
        import httpx

        # TODO: 实现HTTP请求准备逻辑
        url = getattr(tool, 'url', 'http://localhost')
        method = getattr(tool, 'method', 'GET')

        return httpx.Request(method=method, url=url)

    async def process_arguments(self, http_request, tool, args: dict) -> None:
        """处理参数 (对应Go代码中的processArguments)"""
        # TODO: 实现参数处理逻辑
        pass

    async def create_http_client(self, tool):
        """创建HTTP客户端 (对应Go代码中的createHTTPClient)"""
        import httpx

        # TODO: 实现HTTP客户端创建逻辑
        return httpx.AsyncClient(timeout=30.0)

    async def handle_tool_response(
        self, response, tool, tmpl_ctx
    ) -> CallToolResult:
        """处理工具响应 (对应Go代码中的toolRespHandler.Handle)"""
        # TODO: 实现响应处理逻辑
        response_text = response.content.decode('utf-8', errors='ignore')

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=response_text,
                )
            ],
        )

    async def merge_request_info(
        self, session_request: RequestInfo, current_request: Request
    ) -> RequestWrapper:
        """合并请求信息 (对应Go代码中的mergeRequestInfo)"""
        # 初始化wrapper
        wrapper = RequestWrapper(
            headers={},
            query={},
            cookies={},
            path={},
            body={},
        )

        # 合并headers
        if session_request:
            for k, v in session_request.headers.items():
                wrapper.headers[k] = v
        if current_request:
            for k, v in current_request.headers.items():
                wrapper.headers[k] = v

        # 合并query参数
        if session_request:
            for k, v in session_request.queries.items():
                wrapper.query[k] = v
        if current_request:
            for k, v in current_request.query_params.items():
                wrapper.query[k] = v

        # 合并cookies
        if session_request:
            for k, v in session_request.cookies.items():
                wrapper.cookies[k] = v
        if current_request:
            for k, v in current_request.cookies.items():
                wrapper.cookies[k] = v

        return wrapper

    async def handle_mcp(self, request: Request, prefix: str) -> Response:
        """处理MCP端点 (对应Go代码中的handleMCP)"""
        method = request.method

        if method == "OPTIONS":
            return Response(status_code=status.HTTP_200_OK)
        elif method == "GET":
            return await self.handle_get(request, prefix)
        elif method == "POST":
            return await self.handle_post(request, prefix)
        elif method == "DELETE":
            return await self.handle_delete(request, prefix)
        else:
            response = await self.send_protocol_error_with_id(
                "Method not allowed",
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "ConnectionClosed",
            )
            response.headers["Allow"] = "GET, POST, DELETE"
            return response

    async def handle_get(self, request: Request, prefix: str) -> Response:
        """处理GET请求用于SSE流 (对应Go代码中的handleGet)"""
        # 检查Accept头是否包含text/event-stream
        accept_header = request.headers.get("Accept", "")
        if "text/event-stream" not in accept_header:
            return await self.send_protocol_error_with_id(
                "Not Acceptable: Client must accept text/event-stream",
                status.HTTP_406_NOT_ACCEPTABLE,
                "InvalidRequest",
            )

        conn = await self.get_session(request)
        if conn is None:
            return JSONResponse(
                content={"error": "Session not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # TODO: 根据请求头中的last-event-id重放事件

        # TODO: 每个会话只支持一个SSE流，可以在订阅redis主题时检测

        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "Mcp-Session-Id": conn.meta().id,
        }

        async def event_generator():
            try:
                while True:
                    try:
                        # 等待事件
                        event_queue = conn.event_queue()
                        event = await asyncio.wait_for(
                            event_queue.get(),
                            timeout=25.0,  # 减少到25秒
                        )

                        if event is None:
                            continue

                        if event.event == "message":
                            yield f"event: message\ndata: {event.data.decode('utf-8')}\n\n"
                        else:
                            yield f"event: {event.event}\ndata: {event.data.decode('utf-8')}\n\n"

                    except TimeoutError:
                        # 发送心跳
                        logger.debug("发送SSE心跳包（handle_get）")
                        yield "event: heartbeat\ndata: ping\n\n"
                        continue
                    except Exception as e:
                        logger.error(f"Failed to send SSE message: {e}")
                        break

            except asyncio.CancelledError:
                logger.info("SSE stream cancelled")
                raise
            except Exception as e:
                logger.error(f"SSE stream error: {e}")
                raise

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers=headers,
        )

    async def handle_post(self, request: Request, prefix: str) -> Response:
        """处理POST请求包含JSON-RPC消息 (对应Go代码中的handlePost)"""
        # 验证Accept头
        accept = request.headers.get("Accept", "")
        if not (
            ("application/json" in accept or "*/*" in accept)
            and ("text/event-stream" in accept or "*/*" in accept)
        ):
            return await self.send_protocol_error_with_id(
                "Not Acceptable: Client must accept both application/json and text/event-stream",
                status.HTTP_406_NOT_ACCEPTABLE,
                "ConnectionClosed",
            )

        # 验证Content-Type头
        content_type = request.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            return await self.send_protocol_error_with_id(
                "Unsupported Media Type: Content-Type must be application/json",
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                "ConnectionClosed",
            )

        # TODO: 支持批量消息
        try:
            body = await request.body()
            req_data = json.loads(body)

            request_id = req_data.get("id", "")
            jsonrpc_req = JSONRPCRequest(
                jsonrpc=req_data.get("jsonrpc", "2.0"),
                method=req_data["method"],
                params=req_data.get("params"),
                id=request_id,
            )
        except (json.JSONDecodeError, KeyError) as e:
            return await self.send_protocol_error_with_id(
                "Invalid JSON-RPC request",
                status.HTTP_400_BAD_REQUEST,
                "ParseError",
            )

        session_id = request.headers.get("Mcp-Session-Id", "")

        conn = None
        if jsonrpc_req.method == MCP_METHOD_INITIALIZE:
            if session_id:
                # 确认是否已注册
                try:
                    conn = await self.sessions.get(session_id)
                    if conn is not None:
                        return await self.send_protocol_error_with_id(
                            "Invalid Request: Server already initialized",
                            status.HTTP_400_BAD_REQUEST,
                            "InvalidRequest",
                            jsonrpc_req.id,
                        )
                except Exception as e:
                    # 会话不存在或获取失败，继续创建新会话
                    logger.debug(f"Session check failed during initialize: {e}")
            else:
                session_id = str(uuid.uuid4())
                # 从URL路径获取prefix
                path = str(request.url.path)
                prefix = path.rstrip("/mcp")
                if not prefix:
                    prefix = "/"

                request_info = RequestInfo(
                    headers=dict(request.headers.items()),
                    queries=dict(request.query_params.items()),
                    cookies=dict(request.cookies.items()),
                )

                meta = Meta(
                    id=session_id,
                    created_at=datetime.now(),
                    prefix=prefix,
                    type="streamable",
                    request=request_info,
                    extra=None,
                )

                try:
                    conn = await self.sessions.register(meta)
                except Exception as e:
                    return await self.send_protocol_error_with_id(
                        "Failed to create session",
                        status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "InternalError",
                        jsonrpc_req.id,
                    )

            # 设置响应头
            headers = {"Mcp-Session-Id": session_id}
        else:
            try:
                conn = await self.sessions.get(session_id)
                if conn is None:
                    return await self.send_protocol_error_with_id(
                        "Session not found",
                        status.HTTP_404_NOT_FOUND,
                        "RequestTimeout",
                        jsonrpc_req.id,
                    )
            except Exception:
                return await self.send_protocol_error_with_id(
                    "Session not found",
                    status.HTTP_404_NOT_FOUND,
                    "RequestTimeout",
                    jsonrpc_req.id,
                )
            headers = {}

        if conn is None:
            return await self.send_protocol_error_with_id(
                "Failed to get connection",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "InternalError",
                jsonrpc_req.id,
            )

        response = await self.handle_mcp_request(request, jsonrpc_req, conn)

        # 添加会话ID头
        if headers:
            if hasattr(response, 'headers'):
                response.headers.update(headers)

        return response

    async def handle_delete(self, request: Request, prefix: str) -> Response:
        """处理DELETE请求终止会话 (对应Go代码中的handleDelete)"""
        conn = await self.get_session(request)
        if conn is None:
            return JSONResponse(
                content={"error": "Session not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        try:
            await self.sessions.unregister(conn.meta().id)
            return Response(status_code=status.HTTP_200_OK)
        except Exception as e:
            return await self.send_protocol_error_with_id(
                "Failed to terminate session",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "InternalError",
                conn.meta().id,
            )

    async def handle_mcp_request(
        self, request: Request, jsonrpc_req: JSONRPCRequest, conn: Connection
    ) -> Response:
        """处理MCP请求 (对应Go代码中的handleMCPRequest)"""
        method = jsonrpc_req.method

        if method == MCP_METHOD_INITIALIZE:
            # 处理初始化请求
            try:
                result = InitializeResult(
                    protocolVersion=LATEST_PROTOCOL_VERSION,
                    serverInfo=Implementation(
                        name="MyUnla Gateway",
                        version="0.1.0",
                    ),
                    capabilities=ServerCapabilities(
                        tools=ToolsCapability(listChanged=True),
                    ),
                )

                return await self.send_success_response(
                    conn, jsonrpc_req, result, False
                )
            except Exception as e:
                return await self.send_protocol_error_with_id(
                    f"Invalid initialize parameters: {e}",
                    status.HTTP_400_BAD_REQUEST,
                    "InvalidParams",
                    jsonrpc_req.id,
                )

        elif method == MCP_METHOD_INITIALIZED:
            return Response(status_code=status.HTTP_202_ACCEPTED)

        elif method == MCP_METHOD_TOOLS_LIST:
            proto_type = self.state.get_proto_type(conn.meta().prefix)
            if not proto_type:
                return await self.send_protocol_error_with_id(
                    "Server configuration not found",
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "InternalError",
                    jsonrpc_req.id,
                )

            try:
                tools = []
                if proto_type == "http":
                    runtime = self.state.get_runtime(conn.meta().prefix)
                    tools = runtime.tools_schema
                elif proto_type in ["stdio", "sse", "streamable"]:
                    transport = self.state.get_transport(conn.meta().prefix)
                    if transport is None:
                        return await self.send_protocol_error_with_id(
                            "Failed to fetch tools",
                            status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "InternalError",
                            jsonrpc_req.id,
                        )
                    tools = await transport.fetch_tools()
                else:
                    return await self.send_protocol_error_with_id(
                        "Unsupported protocol type",
                        status.HTTP_400_BAD_REQUEST,
                        "InvalidParams",
                        jsonrpc_req.id,
                    )

                result = ListToolsResult(tools=tools)
                return await self.send_success_response(
                    conn, jsonrpc_req, result, False
                )

            except Exception as e:
                return await self.send_protocol_error_with_id(
                    "Failed to fetch tools",
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "InternalError",
                    jsonrpc_req.id,
                )

        elif method == MCP_METHOD_TOOLS_CALL:
            proto_type = self.state.get_proto_type(conn.meta().prefix)
            if not proto_type:
                return await self.send_protocol_error_with_id(
                    "Server configuration not found",
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "InternalError",
                    jsonrpc_req.id,
                )

            # 解析工具调用参数
            try:
                params_data = jsonrpc_req.params or {}
                params = CallToolRequestParams(
                    name=params_data.get("name", ""),
                    arguments=params_data.get("arguments", {}),
                )
                if not params.name:
                    raise ValueError("Missing tool name")
            except Exception as e:
                return await self.send_protocol_error_with_id(
                    f"Invalid tool call parameters: {e}",
                    status.HTTP_400_BAD_REQUEST,
                    "InvalidParams",
                    jsonrpc_req.id,
                )

            try:
                result = None
                if proto_type == "http":
                    result = await self.call_http_tool(
                        request, jsonrpc_req, conn, params
                    )
                elif proto_type in ["stdio", "sse", "streamable"]:
                    transport = self.state.get_transport(conn.meta().prefix)
                    if transport is None:
                        return await self.send_protocol_error_with_id(
                            "Server configuration not found",
                            status.HTTP_404_NOT_FOUND,
                            "MethodNotFound",
                            jsonrpc_req.id,
                        )

                    request_wrapper = await self.merge_request_info(
                        conn.meta().request, request
                    )
                    result = await transport.call_tools(params, request_wrapper)
                else:
                    return await self.send_protocol_error_with_id(
                        "Unsupported protocol type",
                        status.HTTP_400_BAD_REQUEST,
                        "InvalidParams",
                        jsonrpc_req.id,
                    )

                return await self.send_success_response(
                    conn, jsonrpc_req, result, False
                )

            except Exception as e:
                return await self.send_tool_execution_error(
                    conn, jsonrpc_req, e, False
                )

        else:
            return await self.send_protocol_error_with_id(
                "Method not found",
                status.HTTP_404_NOT_FOUND,
                "MethodNotFound",
                jsonrpc_req.id,
            )

    async def get_session(self, request: Request) -> Optional[Connection]:
        """获取会话 (对应Go代码中的getSession)"""
        session_id = request.headers.get("Mcp-Session-Id", "")
        if not session_id:
            logger.warning("Bad Request: Mcp-Session-Id header is required")
            return None

        try:
            conn = await self.sessions.get(session_id)
            if conn is None:
                logger.warning(f"Session not found: {session_id}")
                return None
            return conn
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    async def send_protocol_error(
        self, message: str, status_code: int, error_code: str
    ) -> JSONResponse:
        """发送协议错误响应 (对应Go代码中的sendProtocolError)"""
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": error_code, "message": message}},
        )

    async def send_protocol_error_with_id(
        self,
        message: str,
        status_code: int,
        error_code: str,
        request_id: Optional[Any] = None,
    ) -> JSONResponse:
        """发送带请求ID的协议错误响应"""
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": error_code,
                "message": message,
            },
        }

        if request_id is not None:
            error_response["id"] = request_id

        return JSONResponse(
            status_code=status_code,
            content=error_response,
        )
