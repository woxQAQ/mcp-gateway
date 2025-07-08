from typing import TYPE_CHECKING, Optional

from mcp import ClientSession, Tool
from mcp.client.sse import sse_client
from mcp.types import CallToolRequestParams, CallToolResult, TextContent

from api.mcp import McpServer
from myunla.gateway.transports.base import Transport, transport_has_started
from myunla.templates.context import Context, RequestWrapper
from myunla.utils import get_logger

if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager

logger = get_logger(__name__)


class SSETransport(Transport):
    """基于 MCP 官方 SSE 客户端的传输实现，处理单个 McpServer"""

    def __init__(self, server: McpServer):
        super().__init__(server)
        self._transport: Optional[
            AbstractAsyncContextManager[ClientSession]
        ] = None  # SSE transport
        self._tools_cache: list[Tool] = []

    async def start(self, context: Optional[Context] = None) -> None:
        """启动SSE传输"""
        async with self._lock:
            if self._is_running:
                logger.warning(
                    f"SSE Transport for server {self.server.name} already running"
                )
                return

            try:
                # 创建SSE transport
                await self._create_transport()

                self._is_running = True
                logger.info(
                    f"SSE Transport for server {self.server.name} started successfully"
                )

            except Exception as e:
                logger.error(
                    f"Failed to start SSE Transport for server {self.server.name}: {e}"
                )
                await self.stop()
                raise

    async def stop(self) -> None:
        """停止SSE传输"""
        async with self._lock:
            if not self._is_running:
                return

            try:
                # 清理transport
                if self._transport and hasattr(self._transport, '__aexit__'):
                    try:
                        await self._transport.__aexit__(None, None, None)
                        logger.info(
                            f"Closed transport for server: {self.server.name}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Error closing transport for {self.server.name}: {e}"
                        )

                self._transport = None
                self._tools_cache.clear()

                self._is_running = False
                logger.info(
                    f"SSE Transport for server {self.server.name} stopped"
                )

            except Exception as e:
                logger.error(
                    f"Error during SSE Transport stop for server {self.server.name}: {e}"
                )

    @transport_has_started
    async def fetch_tools(self) -> list[Tool]:
        """从SSE服务器获取工具列表"""
        if not self._transport:
            raise ValueError("Transport not initialized")

        try:
            # 通过transport获取工具
            async with self._transport as session:  # session: ClientSession
                tools_result = await session.list_tools()
                tools = tools_result.tools

                # 缓存工具列表
                self._tools_cache = tools

                logger.info(
                    f"Fetched {len(tools)} tools from server: {self.server.name}"
                )

                return tools

        except Exception as e:
            logger.error(
                f"Failed to fetch tools from server {self.server.name}: {e}"
            )
            raise

    @transport_has_started
    async def call_tools(
        self, call_tool_params: CallToolRequestParams, req: RequestWrapper
    ) -> CallToolResult:
        """调用工具"""
        if not self._transport:
            raise ValueError("Transport not initialized")

        # 检查工具是否存在于此服务器
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
                await self.stop()
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

    async def _create_transport(self) -> None:
        """为服务器创建transport"""
        try:
            # 准备请求头
            headers = {
                "mcp-protocol-version": "1.0",
            }

            # 创建 SSE 客户端传输
            transport = sse_client(
                url=self.server.url,
                headers=headers,
                timeout=30.0,
                sse_read_timeout=300.0,
            )

            # 存储transport
            self._transport = transport

            logger.info(f"Created SSE transport for server: {self.server.name}")

        except Exception as e:
            logger.error(
                f"Error creating transport for SSE server {self.server.name}: {e}"
            )
            raise

    def _has_tool(self, tool_name: str) -> bool:
        """检查服务器是否有指定的工具"""
        return any(tool.name == tool_name for tool in self._tools_cache)
