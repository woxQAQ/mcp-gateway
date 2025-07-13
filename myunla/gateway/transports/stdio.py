import shlex
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Optional

from mcp import ClientSession, Tool
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolRequestParams, CallToolResult, TextContent

from api.mcp import McpServer
from myunla.gateway.transports.base import Transport, transport_has_started
from myunla.templates.context import Context, RequestWrapper
from myunla.utils import get_logger

if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager

logger = get_logger(__name__)


class StdIOTransport(Transport):
    """基于 MCP 官方 STDIO 客户端的传输实现，处理单个 McpServer"""

    def __init__(self, server: McpServer):
        super().__init__(server)
        self._transport: Optional[
            AbstractAsyncContextManager[ClientSession]
        ] = None
        self._tools_cache: list[Tool] = []

    async def start(self, context: Optional[Context] = None) -> None:
        """启动STDIO传输"""
        async with self._lock:
            if self._transport:
                logger.warning(
                    f"STDIO Transport for server {self.server.name} already running"
                )
                return

            try:
                # 创建STDIO transport
                await self._create_transport()
                if not self._transport:
                    raise ValueError("Transport not initialized")

                logger.info(
                    f"STDIO Transport for server {self.server.name} started successfully"
                )
                async with self._transport as session:
                    await session.initialize()

            except Exception as e:
                logger.error(
                    f"Failed to start STDIO Transport for server {self.server.name}: {e}"
                )
                await self.stop()
                raise

    async def stop(self) -> None:
        """停止STDIO传输"""
        async with self._lock:
            if not self._transport:
                return

            try:
                # 清理transport
                await self._transport.__aexit__(None, None, None)
                self._transport = None
                self._tools_cache.clear()

                logger.info(
                    f"STDIO Transport for server {self.server.name} stopped"
                )

            except Exception as e:
                logger.error(
                    f"Error during STDIO Transport stop for server {self.server.name}: {e}"
                )

    @transport_has_started
    async def fetch_tools(self) -> list[Tool]:
        """从STDIO服务器获取工具列表"""
        if not self._transport:
            raise ValueError("Transport not initialized")

        try:
            # 通过transport获取工具
            async with self._transport as session:  # session: ClientSession
                tools_result = await session.list_tools()
                tools = tools_result.tools
                # 缓存工具列表
                self._tools_cache = tools
                await self.stop()
        except Exception as e:
            logger.error(
                f"Failed to fetch tools from server {self.server.name}: {e}"
            )
            raise

        return tools

    @transport_has_started
    async def call_tools(
        self, call_tool_params: CallToolRequestParams, req: RequestWrapper
    ) -> CallToolResult:
        """调用工具"""
        # 检查工具是否存在于此服务器
        if not self._transport:
            raise ValueError("Transport not initialized")

        tool_name = call_tool_params.name
        if not self._has_tool(tool_name):
            # 返回错误格式的 MCP tool 结果
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Tool {tool_name} not found on server {self.server.name}",
                    )
                ],
                isError=True,
            )

        try:
            # 使用transport调用工具
            async with self._transport as session:  # session: ClientSession
                await session.initialize()
                result = await session.call_tool(
                    call_tool_params.name, call_tool_params.arguments or {}
                )

                logger.info(
                    f"Successfully called tool {tool_name} on server {self.server.name}"
                )
                return result

        except Exception as e:
            logger.error(
                f"Failed to call tool {tool_name} on server {self.server.name}: {e}"
            )
            # 返回错误格式的 MCP tool 结果
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error calling tool {tool_name}: {e!s}",
                    )
                ],
                isError=True,
            )

    @asynccontextmanager
    async def _create_client_session(self):
        """创建客户端会话的异步上下文管理器"""
        # 解析命令和参数
        command_args = self._parse_command(self.server.command)
        if not command_args:
            raise ValueError(f"Invalid command: {self.server.command}")

        command = command_args[0]
        args = command_args[1:]

        # 创建服务器参数
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=None,  # 使用默认环境变量
            cwd=None,  # 使用当前工作目录
            encoding="utf-8",
            encoding_error_handler="strict",
        )

        # 使用 stdio_client 获取读写流
        async with stdio_client(server_params) as (read_stream, write_stream):
            # 创建 ClientSession
            session = ClientSession(read_stream, write_stream)
            try:
                yield session
            finally:
                # 会话清理会由 stdio_client 上下文管理器处理
                pass

    async def _create_transport(self) -> None:
        """为服务器创建transport"""
        try:
            # 创建自定义的异步上下文管理器
            self._transport = self._create_client_session()

            logger.info(
                f"Created STDIO transport for server: {self.server.name}"
            )

        except Exception as e:
            logger.error(
                f"Error creating transport for STDIO server {self.server.name}: {e}"
            )
            raise

    def _parse_command(self, command: str) -> list[str]:
        """解析命令字符串为命令和参数列表"""
        try:
            # 使用 shlex 来正确处理带引号的参数
            return shlex.split(command)
        except ValueError as e:
            logger.error(f"Failed to parse command '{command}': {e}")
            return []

    def _has_tool(self, tool_name: str) -> bool:
        """检查服务器是否有指定的工具"""
        return any(tool.name == tool_name for tool in self._tools_cache)
