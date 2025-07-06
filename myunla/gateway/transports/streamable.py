"""
Streamable Transport 实现

支持流式工具调用和实时响应的 MCP 传输层
"""

from typing import TYPE_CHECKING, Optional

from mcp import ClientSession, Tool
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import CallToolRequestParams, CallToolResult, TextContent

from api.mcp import McpServer
from myunla.gateway.transports.base import Transport, transport_has_started
from myunla.templates.context import Context, RequestWrapper
from myunla.utils import get_logger

if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager

logger = get_logger(__name__)


class StreamableTransport(Transport):
    """支持流式响应的 MCP 传输实现"""

    def __init__(self, server: McpServer):
        super().__init__(server)
        self._transport: Optional[
            AbstractAsyncContextManager[ClientSession]
        ] = None
        self._tools_cache: list[Tool] = []

    async def start(self, context: Optional[Context] = None) -> None:
        """启动流式传输"""
        async with self._lock:
            if self._is_running:
                logger.warning(
                    f"Streamable Transport for server {self.server.name} already running"
                )
                return

            try:
                # 创建底层传输
                await self._create_transport()

                self._is_running = True
                logger.info(
                    f"Streamable Transport for server {self.server.name} started successfully"
                )

            except Exception as e:
                logger.error(
                    f"Failed to start Streamable Transport for server {self.server.name}: {e}"
                )
                await self.stop()
                raise

    async def stop(self) -> None:
        """停止流式传输"""
        async with self._lock:
            if not self._is_running:
                return

            try:
                # 清理底层传输
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
                    f"Streamable Transport for server {self.server.name} stopped"
                )

            except Exception as e:
                logger.error(
                    f"Error during Streamable Transport stop for server {self.server.name}: {e}"
                )

    @transport_has_started
    async def fetch_tools(self) -> list[Tool]:
        """获取工具列表"""
        try:
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
        """调用工具（非流式）"""
        tool_name = call_tool_params.name
        if not self._has_tool(tool_name):
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
        """创建底层传输"""
        try:
            headers = {
                "mcp-protocol-version": "1.0",
                "X-Streaming-Support": "true",  # 标识支持流式
            }

            # 基于服务器类型创建传输
            if self.server.type.value == "sse":
                transport = streamablehttp_client(
                    url=self.server.url,
                    headers=headers,
                    timeout=30.0,
                )
            else:
                # 其他类型的传输可以在这里添加
                raise ValueError(
                    f"Unsupported server type for streaming: {self.server.type.value}"
                )

            self._transport = transport
            logger.info(
                f"Created streamable transport for server: {self.server.name}"
            )

        except Exception as e:
            logger.error(
                f"Error creating streamable transport for server {self.server.name}: {e}"
            )
            raise

    def _has_tool(self, tool_name: str) -> bool:
        """检查服务器是否有指定的工具"""
        return any(tool.name == tool_name for tool in self._tools_cache)
