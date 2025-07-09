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
    """
    构建状态时发生的异常

    当在构建MCP服务器状态时遇到错误（如传输层创建失败、服务器配置错误等）
    时抛出此异常。提供了详细的上下文信息来帮助定位问题。
    """

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
            prefix: 出错的前缀路由
            server_name: 出错的服务器名称
            tenant_name: 出错的租户名称
            error_type: 错误类型分类
        """
        super().__init__(message)
        self.prefix = prefix
        self.server_name = server_name
        self.tenant_name = tenant_name
        self.error_type = error_type

    def __str__(self) -> str:
        """
        返回详细的错误信息

        格式化异常信息，包含所有可用的上下文信息，便于调试和问题定位。
        """
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
    """
    后端协议类型枚举

    定义了系统支持的各种传输协议类型，用于确定如何与MCP服务器通信。
    """

    HTTP = "http"  # HTTP协议，用于RESTful API通信
    SSE = "sse"  # Server-Sent Events，用于服务器推送
    STREAMABLE = "streamable"  # 流式传输协议
    STDIO = "stdio"  # 标准输入输出，用于本地进程通信
    GRPC = "grpc"  # gRPC协议，高性能RPC通信


class Metrics(BaseModel):
    """
    系统状态指标

    收集和跟踪系统运行时的各种指标数据，用于监控和性能分析。
    """

    total_tools: int = 0  # 系统中注册的工具总数
    http_servers: int = 0  # HTTP服务器总数
    mcp_servers: int = 0  # MCP服务器总数
    idle_http_servers: int = 0  # 空闲的HTTP服务器数量（未绑定路由）
    idle_mcp_servers: int = 0  # 空闲的MCP服务器数量（未绑定路由）
    missing_tools: int = 0  # 缺失的工具数量（配置中引用但未找到）


class Runtime(BaseModel):
    """
    运行时配置管理

    管理单个路由前缀的完整运行时状态，包括协议类型、服务器配置、
    工具集合和传输层等。每个路由前缀对应一个Runtime实例。
    """

    backend_proto: BackendProto  # 后端协议类型
    router: Router  # 路由器配置
    http_server: Optional[HttpServer] = (
        None  # HTTP服务器配置（如果使用HTTP协议）
    )
    mcp_server: Optional[McpServer] = None  # MCP服务器配置（如果使用MCP协议）

    tools: dict[str, Tool]  # 可用工具映射（工具名 -> 工具对象）
    tools_schema: list[ToolType]  # 工具schema列表，用于API文档生成

    transport: Optional[Transport] = None  # 传输层实例，负责实际通信

    def update(self, **kwargs) -> None:
        """
        根据传入的字段更新runtime配置

        批量更新Runtime对象的属性，仅更新存在的字段。

        Args:
            **kwargs: 要更新的字段和值

        Raises:
            ValueError: 当尝试更新不存在的字段时
        """
        for field_name, value in kwargs.items():
            if hasattr(self, field_name):
                setattr(self, field_name, value)
            else:
                raise ValueError(f"Runtime has no field '{field_name}'")


class State(BaseModel):
    """
    全局状态管理器

    管理整个MCP网关系统的状态，包括所有MCP配置、运行时实例、
    指标数据等。提供状态构建、查询和更新的核心功能。

    主要职责：
    1. 解析和验证MCP配置
    2. 构建和管理运行时实例
    3. 处理服务器生命周期（启动、停止、重用）
    4. 维护路由和工具映射关系
    5. 收集和报告系统指标
    """

    mcps: list[Mcp]  # MCP配置列表
    runtime: dict[str, Runtime]  # 运行时映射（前缀 -> Runtime）
    metrics: Metrics  # 系统指标
    raw_configs: Optional[list[Mcp]] = None  # 原始配置备份，用于调试

    def get_runtime(self, prefix: str) -> Runtime:
        """
        获取指定前缀的运行时配置，如果不存在则创建新的

        确保每个路由前缀都有对应的Runtime实例，使用懒加载模式。

        Args:
            prefix: 路由前缀

        Returns:
            Runtime: 对应的运行时配置对象
        """
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
        """
        获取指定前缀的SSE前缀配置

        用于Server-Sent Events连接的路由配置。

        Args:
            prefix: 路由前缀

        Returns:
            str: SSE前缀，如果未配置则返回空字符串
        """
        runtime = self.runtime.get(prefix)
        if runtime and runtime.router:
            return runtime.router.sse_prefix
        return ""

    def get_proto_type(self, prefix: str) -> Optional[str]:
        """
        获取指定前缀的协议类型

        Args:
            prefix: 路由前缀

        Returns:
            Optional[str]: 协议类型字符串，如果未找到则返回None
        """
        runtime = self.runtime.get(prefix)
        if runtime:
            return runtime.backend_proto.value
        return None

    def get_transport(self, prefix: str) -> Optional[Transport]:
        """
        获取指定前缀的传输层实例

        Args:
            prefix: 路由前缀

        Returns:
            Optional[Transport]: 传输层实例，如果未找到则返回None
        """
        runtime = self.runtime.get(prefix)
        if runtime:
            return runtime.transport
        return None

    def setRouter(self, prefix: str, router: Router) -> None:
        """
        设置路由器配置

        为指定前缀设置路由器配置，如果Runtime不存在会自动创建。

        Args:
            prefix: 路由前缀
            router: 路由器配置对象
        """
        runtime = self.get_runtime(prefix)
        runtime.router = router

    def _find_router_by_prefix(self, prefix: str) -> Optional[Router]:
        """
        查找指定前缀的路由器

        在所有MCP配置中搜索匹配指定前缀的路由器。

        Args:
            prefix: 要查找的前缀

        Returns:
            Optional[Router]: 匹配的路由器，如果未找到则返回None
        """
        for mcp in self.mcps:
            for router in mcp.routers:
                if router.prefix == prefix:
                    return router
        return None

    def _build_prefix_map(self, mcp: Mcp) -> dict[str, list[str]]:
        """
        构建前缀映射：服务器名称 -> 前缀集合

        分析MCP配置中的路由器，建立服务器名称到前缀的映射关系。
        这个映射用于确定哪些前缀需要绑定到哪个服务器。

        Args:
            mcp: MCP配置对象

        Returns:
            dict[str, list[str]]: 服务器名称到前缀列表的映射
        """
        prefix_map: dict[str, list[str]] = {}

        # 遍历所有路由器，建立服务器到前缀的映射
        for router in mcp.routers:
            server_name = router.server
            if server_name not in prefix_map:
                prefix_map[server_name] = []
            prefix_map[server_name].append(router.prefix)

            # 注册路由器到状态中
            self.setRouter(router.prefix, router)
            logger.info(
                f"Registered router - tenant: {mcp.tenant_name}, prefix: {router.prefix}, server: {server_name}"
            )

        # 去重前缀列表
        for server_name, prefixes in prefix_map.items():
            prefix_map[server_name] = list(set(prefixes))

        return prefix_map

    def _process_http_servers(
        self, mcp: Mcp, prefix_map: dict[str, list[str]], tools: dict[str, Tool]
    ) -> None:
        """
        处理HTTP服务器配置

        为每个HTTP服务器创建对应的Runtime实例，配置工具集合和schema。

        Args:
            mcp: MCP配置对象
            prefix_map: 服务器名称到前缀的映射
            tools: 可用工具映射
        """
        self.metrics.http_servers += len(mcp.http_servers)

        for server in mcp.http_servers:
            # 查找服务器对应的前缀
            prefixes = prefix_map.get(server.name, [])
            if not prefixes:
                self.metrics.idle_http_servers += 1
                logger.warning(
                    f"Failed to find prefix for server {server.name}"
                )
                continue

            # 构建服务器允许使用的工具集合
            _tools, _tool_schemas = self._build_allowed_tools(server, tools)

            # 为每个前缀创建或更新Runtime
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
        """
        构建服务器允许使用的工具列表和schema

        根据服务器配置中指定的工具名称，从全局工具集合中筛选出
        该服务器可以使用的工具，并生成对应的schema。

        Args:
            server: HTTP服务器配置
            tools: 全局工具映射

        Returns:
            tuple: (允许的工具映射, 工具schema列表)
        """
        allowed_tool_schemas: list[ToolType] = []
        allowed_tools: dict[str, Tool] = {}

        for tool_name in server.tools:
            tool = tools.get(tool_name)
            if tool:
                # 工具存在，添加到允许列表
                allowed_tool_schemas.append(tool.to_tool_type())
                allowed_tools[tool_name] = tool
            else:
                # 工具缺失，记录警告和指标
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
        """
        处理MCP服务器配置

        为每个MCP服务器创建传输层和Runtime实例，处理服务器的
        启动策略和生命周期管理。

        Args:
            mcp: MCP配置对象
            prefix_map: 服务器名称到前缀的映射
            old_state: 旧的状态对象，用于复用传输层
        """
        self.metrics.mcp_servers += len(mcp.servers)

        for mcp_server in mcp.servers:
            # 查找服务器对应的前缀
            prefixes = prefix_map.get(mcp_server.name, [])
            if not prefixes:
                self.metrics.idle_mcp_servers += 1
                logger.warning(
                    f"Failed to find prefix for mcp server {mcp_server.name}"
                )
                continue

            # 为每个前缀创建Runtime
            await self._create_mcp_runtimes(mcp_server, prefixes, old_state)

    async def _create_mcp_runtimes(
        self,
        mcp_server: McpServer,
        prefixes: list[str],
        old_state: Optional["State"],
    ) -> None:
        """
        为MCP服务器创建运行时实例

        为服务器的每个前缀创建Runtime，包括传输层创建、
        协议类型设置和启动策略处理。

        Args:
            mcp_server: MCP服务器配置
            prefixes: 服务器绑定的前缀列表
            old_state: 旧状态，用于传输层复用
        """
        for prefix in prefixes:
            runtime = self.get_runtime(prefix)

            try:
                # 获取或创建传输层（优先复用旧的）
                transport = self._get_or_create_transport(
                    mcp_server, prefix, old_state
                )

                # 确定后端协议类型
                backend_proto = self._get_backend_proto_for_server(mcp_server)

                # 更新Runtime配置
                runtime.update(
                    backend_proto=backend_proto,
                    mcp_server=mcp_server,
                    transport=transport,
                )

                # 处理服务器启动策略
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
        """
        获取或创建传输层实例

        优先复用旧状态中的传输层（如果配置相同），否则创建新的。
        这个策略可以避免不必要的连接重建，提高性能。

        Args:
            mcp_server: MCP服务器配置
            prefix: 路由前缀
            old_state: 旧状态对象

        Returns:
            Transport: 传输层实例

        Raises:
            BuildStateException: 传输层创建失败时
        """
        transport = None

        # 尝试从旧状态复用传输层
        if old_state:
            old_runtime = old_state.runtime.get(prefix)
            if old_runtime and old_runtime.mcp_server:
                old_server = old_runtime.mcp_server
                # 检查服务器配置是否相同
                if (
                    old_server.type == mcp_server.type
                    and old_server.command == mcp_server.command
                    and old_server.url == mcp_server.url
                    and len(old_server.args) == len(mcp_server.args)
                ):
                    if old_server.args == mcp_server.args:
                        # 配置完全相同，复用传输层
                        transport = old_runtime.transport
                        logger.info(
                            f"Reusing transport for server {mcp_server.name}"
                        )

        # 创建新的传输层
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
        """
        根据服务器类型确定后端协议

        Args:
            mcp_server: MCP服务器配置

        Returns:
            BackendProto: 对应的后端协议类型
        """
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
        """
        处理MCP服务器启动策略

        根据服务器的启动策略（ON_START或preinstalled）决定
        是否立即启动服务器或仅验证其可用性。

        Args:
            mcp_server: MCP服务器配置
            prefix: 路由前缀
            transport: 传输层实例
        """
        try:
            if mcp_server.policy == Policy.ON_START:
                # 立即启动并保持运行
                await self._start_mcp_server(
                    mcp_server, prefix, transport, keep_running=True
                )
            elif mcp_server.preinstalled:
                # 验证预安装服务器的可用性
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
        """
        启动MCP服务器

        根据keep_running参数决定是持续运行还是仅验证后停止。

        Args:
            mcp_server: MCP服务器配置
            prefix: 路由前缀
            transport: 传输层实例
            keep_running: 是否保持运行状态
        """
        if transport.is_running:
            return

        try:
            await transport.start()
            if keep_running:
                logger.info(
                    f"Started MCP server {mcp_server.name} with policy ON_START"
                )
            else:
                # 仅验证后停止
                await transport.stop()
                logger.info(
                    f"Verified preinstalled MCP server {mcp_server.name}"
                )
        except Exception as e:
            logger.error(f"Failed to start MCP server {mcp_server.name}: {e}")
            raise

    async def _cleanup_unused_transports(self, old_state: "State") -> None:
        """
        清理不再使用的传输层

        比较新旧状态，关闭在新状态中不再需要的传输层连接，
        释放资源并避免资源泄漏。

        Args:
            old_state: 旧的状态对象
        """
        for prefix, old_runtime in old_state.runtime.items():
            # 检查前缀是否在新状态中存在
            if prefix not in self.runtime:
                if old_runtime.mcp_server is None:
                    continue
                if old_runtime.transport is None:
                    logger.info(
                        f"Transport already stopped for prefix {prefix}, command: {old_runtime.mcp_server.command}"
                    )
                    continue

                # 关闭不再使用的传输层
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
        """
        从MCP配置列表构建State对象

        这是状态构建的主入口方法，负责：
        1. 解析MCP配置
        2. 构建前缀映射关系
        3. 创建HTTP和MCP服务器的Runtime
        4. 处理传输层的复用和清理
        5. 收集和报告系统指标

        Args:
            mcps: MCP配置列表
            old_state: 旧的状态对象，用于传输层复用

        Returns:
            State: 构建完成的新状态对象
        """
        # 初始化新状态
        state = cls(mcps=mcps, runtime={}, metrics=Metrics(), raw_configs=mcps)

        # 处理每个MCP配置
        for mcp in mcps:
            # 构建工具映射
            tools: dict[str, Tool] = {tool.name: tool for tool in mcp.tools}
            state.metrics.total_tools += len(mcp.tools)

            # 构建服务器到前缀的映射关系
            prefix_map = state._build_prefix_map(mcp)

            # 处理HTTP服务器
            state._process_http_servers(mcp, prefix_map, tools)

            # 处理MCP服务器（异步）
            await state._process_mcp_servers(mcp, prefix_map, old_state)

        # 清理旧状态中不再使用的传输层
        if old_state:
            try:
                await state._cleanup_unused_transports(old_state)
            except Exception as e:
                logger.error(f"Failed to cleanup unused transports: {e}")

        logger.info(f"Built state with metrics: {state.metrics}")
        return state
