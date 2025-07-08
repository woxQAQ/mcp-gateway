from enum import StrEnum
from typing import Optional

from mcp.types import Tool as ToolType
from pydantic import BaseModel

from api.enums import Policy
from api.mcp import HttpServer, Mcp, McpServer, Router, Tool
from myunla.gateway.transports import create_transport
from myunla.gateway.transports.base import Transport
from myunla.utils import get_logger

logger = get_logger(__name__)


class BuildStateException(Exception):
    """构建状态时发生的异常"""

    def __init__(
        self,
        message: str,
        *,
        prefix: Optional[str] = None,
        server_name: Optional[str] = None,
        tenant_name: Optional[str] = None,
        error_type: Optional[str] = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            prefix: 出错的前缀
            server_name: 出错的服务器名称
            tenant_name: 出错的租户名称
            error_type: 错误类型
        """
        super().__init__(message)
        self.prefix = prefix
        self.server_name = server_name
        self.tenant_name = tenant_name
        self.error_type = error_type

    def __str__(self) -> str:
        """返回详细的错误信息"""
        parts = [super().__str__()]

        if self.tenant_name:
            parts.append(f"tenant: {self.tenant_name}")
        if self.server_name:
            parts.append(f"server: {self.server_name}")
        if self.prefix:
            parts.append(f"prefix: {self.prefix}")
        if self.error_type:
            parts.append(f"type: {self.error_type}")

        if len(parts) > 1:
            return f"{parts[0]} ({', '.join(parts[1:])})"
        return parts[0]


class BackendProto(StrEnum):
    HTTP = "http"
    SSE = "sse"
    STREAMABLE = "streamable"
    STDIO = "stdio"
    GRPC = "grpc"


class Metrics(BaseModel):
    """状态指标"""

    total_tools: int = 0
    http_servers: int = 0
    mcp_servers: int = 0
    idle_http_servers: int = 0
    idle_mcp_servers: int = 0
    missing_tools: int = 0


class Runtime(BaseModel):
    backend_proto: BackendProto
    router: Router
    http_server: Optional[HttpServer] = None
    mcp_server: Optional[McpServer] = None

    tools: dict[str, Tool]
    tools_schema: list[ToolType]

    transport: Optional[Transport] = None

    def update(self, **kwargs) -> None:
        """根据传入的字段更新runtime配置"""
        for field_name, value in kwargs.items():
            if hasattr(self, field_name):
                setattr(self, field_name, value)
            else:
                raise ValueError(f"Runtime has no field '{field_name}'")


class State(BaseModel):
    mcps: list[Mcp]
    runtime: dict[str, Runtime]
    metrics: Metrics
    raw_configs: Optional[list[Mcp]] = None

    def get_runtime(self, prefix: str) -> Runtime:
        """获取指定前缀的运行时配置，如果不存在则创建新的"""
        runtime = self.runtime.get(prefix)
        if runtime is None:
            # 创建一个带有默认值的Runtime
            runtime = Runtime(
                backend_proto=BackendProto.HTTP,
                router=Router(prefix=prefix, server="", sse_prefix=""),
                tools={},
                tools_schema=[],
            )
            self.runtime[prefix] = runtime
        return runtime

    def get_sse_prefix(self, prefix: str) -> str:
        """获取指定前缀的SSE前缀配置"""
        runtime = self.runtime.get(prefix)
        if runtime and runtime.router:
            return runtime.router.sse_prefix
        return ""

    def get_proto_type(self, prefix: str) -> Optional[str]:
        """获取指定前缀的协议类型"""
        runtime = self.runtime.get(prefix)
        if runtime:
            return runtime.backend_proto.value
        return None

    def get_transport(self, prefix: str) -> Optional[Transport]:
        """获取指定前缀的传输层"""
        runtime = self.runtime.get(prefix)
        if runtime:
            return runtime.transport
        return None

    def setRouter(self, prefix: str, router: Router) -> None:
        """设置路由器配置"""
        runtime = self.get_runtime(prefix)
        runtime.router = router

    def _find_router_by_prefix(self, prefix: str) -> Optional[Router]:
        """查找指定前缀的路由器"""
        for mcp in self.mcps:
            for router in mcp.routers:
                if router.prefix == prefix:
                    return router
        return None

    def _build_prefix_map(self, mcp: Mcp) -> dict[str, list[str]]:
        """构建前缀映射：服务器名称 -> 前缀集合"""
        prefix_map: dict[str, list[str]] = {}

        for router in mcp.routers:
            server_name = router.server
            if server_name not in prefix_map:
                prefix_map[server_name] = []
            prefix_map[server_name].append(router.prefix)
            self.setRouter(router.prefix, router)
            logger.info(
                f"Registered router - tenant: {mcp.tenant_name}, prefix: {router.prefix}, server: {server_name}"
            )

        for server_name, prefixes in prefix_map.items():
            prefix_map[server_name] = list(set(prefixes))

        return prefix_map

    def _process_http_servers(
        self, mcp: Mcp, prefix_map: dict[str, list[str]], tools: dict[str, Tool]
    ) -> None:
        """处理HTTP服务器"""
        self.metrics.http_servers += len(mcp.http_servers)

        for server in mcp.http_servers:
            prefixes = prefix_map.get(server.name, [])
            if not prefixes:
                self.metrics.idle_http_servers += 1
                logger.warning(
                    f"Failed to find prefix for server {server.name}"
                )
                continue

            _tools, _tool_schemas = self._build_allowed_tools(server, tools)

            for prefix in prefixes:
                runtime = self.get_runtime(prefix=prefix)

                runtime.update(
                    backend_proto=BackendProto.HTTP,
                    http_server=server,
                    tools=_tools,
                    tools_schema=_tool_schemas,
                )

    def _build_allowed_tools(
        self, server: HttpServer, tools: dict[str, Tool]
    ) -> tuple[dict[str, Tool], list[ToolType]]:
        """构建允许的工具列表和schema"""
        allowed_tool_schemas: list[ToolType] = []
        allowed_tools: dict[str, Tool] = {}

        for tool_name in server.tools:
            tool = tools.get(tool_name)
            if tool:
                allowed_tool_schemas.append(tool.to_tool_type())
                allowed_tools[tool_name] = tool
            else:
                self.metrics.missing_tools += 1
                logger.warning(
                    f"Failed to find allowed tool for server {server.name}, tool: {tool_name}"
                )

        return allowed_tools, allowed_tool_schemas

    async def _process_mcp_servers(
        self,
        mcp: Mcp,
        prefix_map: dict[str, list[str]],
        old_state: Optional["State"],
    ) -> None:
        """处理MCP服务器"""
        self.metrics.mcp_servers += len(mcp.servers)

        for mcp_server in mcp.servers:
            prefixes = prefix_map.get(mcp_server.name, [])
            if not prefixes:
                self.metrics.idle_mcp_servers += 1
                logger.warning(
                    f"Failed to find prefix for mcp server {mcp_server.name}"
                )
                continue

            await self._create_mcp_runtimes(mcp_server, prefixes, old_state)

    async def _create_mcp_runtimes(
        self,
        mcp_server: McpServer,
        prefixes: list[str],
        old_state: Optional["State"],
    ) -> None:
        """为MCP服务器创建运行时"""
        for prefix in prefixes:
            runtime = self.get_runtime(prefix)

            try:
                transport = self._get_or_create_transport(
                    mcp_server, prefix, old_state
                )

                backend_proto = self._get_backend_proto_for_server(mcp_server)

                runtime.update(
                    backend_proto=backend_proto,
                    mcp_server=mcp_server,
                    transport=transport,
                )

                await self._handle_mcp_server_startup(
                    mcp_server, prefix, transport
                )

            except BuildStateException as e:
                logger.error(f"Failed to create MCP runtime: {e}")
                continue
            except Exception as e:
                logger.error(
                    f"Unexpected error creating MCP runtime for {mcp_server.name}, prefix {prefix}: {e}"
                )
                continue

    def _get_or_create_transport(
        self, mcp_server: McpServer, prefix: str, old_state: Optional["State"]
    ) -> Transport:
        """获取或创建transport"""
        transport = None
        if old_state:
            old_runtime = old_state.runtime.get(prefix)
            if old_runtime and old_runtime.mcp_server:
                old_server = old_runtime.mcp_server
                if (
                    old_server.type == mcp_server.type
                    and old_server.command == mcp_server.command
                    and old_server.url == mcp_server.url
                    and len(old_server.args) == len(mcp_server.args)
                ):
                    if old_server.args == mcp_server.args:
                        transport = old_runtime.transport
                        logger.info(
                            f"Reusing transport for server {mcp_server.name}"
                        )

        if transport is None:
            try:
                transport = create_transport(mcp_server)
            except Exception as e:
                raise BuildStateException(
                    f"Failed to create transport for server {mcp_server.name}: {e}",
                    server_name=mcp_server.name,
                    error_type="transport_creation_failed",
                ) from e

        return transport

    def _get_backend_proto_for_server(
        self, mcp_server: McpServer
    ) -> BackendProto:
        """设置后端协议类型"""
        if mcp_server.type == "sse":
            return BackendProto.SSE
        elif mcp_server.type == "stdio":
            return BackendProto.STDIO
        elif mcp_server.type == "streamable":
            return BackendProto.STREAMABLE
        else:
            return BackendProto.HTTP

    async def _handle_mcp_server_startup(
        self, mcp_server: McpServer, prefix: str, transport: Transport
    ) -> None:
        """处理MCP服务器启动策略"""
        try:
            if mcp_server.policy == Policy.ON_START:
                await self._start_mcp_server(
                    mcp_server, prefix, transport, keep_running=True
                )
            elif mcp_server.preinstalled:
                await self._start_mcp_server(
                    mcp_server, prefix, transport, keep_running=False
                )
        except Exception as e:
            logger.error(
                f"Failed to handle startup for server {mcp_server.name}, prefix {prefix}: {e}"
            )

    async def _start_mcp_server(
        self,
        mcp_server: McpServer,
        prefix: str,
        transport: Transport,
        keep_running: bool,
    ) -> None:
        """启动MCP服务器"""
        if transport.is_running:
            return

        try:
            await transport.start()
            if keep_running:
                logger.info(
                    f"Started MCP server {mcp_server.name} with policy ON_START"
                )
            else:
                await transport.stop()
                logger.info(
                    f"Verified preinstalled MCP server {mcp_server.name}"
                )
        except Exception as e:
            logger.error(f"Failed to start MCP server {mcp_server.name}: {e}")
            raise

    async def _cleanup_unused_transports(self, old_state: "State") -> None:
        """清理不再使用的transport"""
        for prefix, old_runtime in old_state.runtime.items():
            if prefix not in self.runtime:
                if old_runtime.mcp_server is None:
                    continue
                if old_runtime.transport is None:
                    logger.info(
                        f"Transport already stopped for prefix {prefix}, command: {old_runtime.mcp_server.command}"
                    )
                    continue
                logger.info(
                    f"Shutting down unused transport for prefix {prefix}, command: {old_runtime.mcp_server.command}"
                )
                try:
                    await old_runtime.transport.stop()
                except Exception as e:
                    logger.warning(
                        f"Failed to close old transport for prefix {prefix}: {e}, command: {old_runtime.mcp_server.command}"
                    )

    @classmethod
    async def build_from_mcp(
        cls, mcps: list[Mcp], old_state: Optional["State"] = None
    ) -> "State":
        """从MCP配置列表构建State对象"""
        state = cls(mcps=mcps, runtime={}, metrics=Metrics(), raw_configs=mcps)

        for mcp in mcps:
            tools: dict[str, Tool] = {tool.name: tool for tool in mcp.tools}
            state.metrics.total_tools += len(mcp.tools)

            prefix_map = state._build_prefix_map(mcp)

            state._process_http_servers(mcp, prefix_map, tools)

            await state._process_mcp_servers(mcp, prefix_map, old_state)

        if old_state:
            try:
                await state._cleanup_unused_transports(old_state)
            except Exception as e:
                logger.error(f"Failed to cleanup unused transports: {e}")

        logger.info(f"Built state with metrics: {state.metrics}")
        return state
