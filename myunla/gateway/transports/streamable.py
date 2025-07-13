"""
Streamable Transport 实现

支持流式工具调用和实时响应的 MCP 传输层
"""

from contextlib import asynccontextmanager
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
            if self._transport:
                logger.warning(
                    f"Streamable Transport for server {self.server.name} already running"
                )
                return

            try:
                # 创建底层传输
                await self._create_transport()
                if not self._transport:
                    raise ValueError("Transport not initialized")

                logger.info(
                    f"Streamable Transport for server {self.server.name} started successfully"
                )
                async with self._transport as session:
                    await session.initialize()

            except Exception as e:
                logger.error(
                    f"Failed to start Streamable Transport for server {self.server.name}: {e}"
                )
                await self.stop()
                raise

    async def stop(self) -> None:
        """停止流式传输"""
        async with self._lock:
            if not self._transport:
                return

            try:
                # 清理底层传输
                await self._transport.__aexit__(None, None, None)
                self._transport = None
                self._tools_cache.clear()

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
        if not self._transport:
            raise ValueError("Transport not initialized")

        try:
            async with self._transport as session:
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
        """调用工具（非流式）"""
        if not self._transport:
            raise ValueError("Transport not initialized")

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

    @asynccontextmanager
    async def _create_client_session(self):
        """创建客户端会话的异步上下文管理器"""
        headers = {
            "mcp-protocol-version": "1.0",
            "X-Streaming-Support": "true",  # 标识支持流式
        }

        # 基于服务器类型创建传输
        if self.server.type.value == "sse":
            # 使用 streamablehttp_client 获取读写流
            async with streamablehttp_client(
                url=self.server.url,
                headers=headers,
                timeout=30.0,
            ) as streams:
                # 解构 streamablehttp_client 返回的流和回调函数
                read_stream, write_stream, *_ = streams

                # 创建 ClientSession
                session = ClientSession(read_stream, write_stream)
                try:
                    yield session
                finally:
                    # 会话清理会由 streamablehttp_client 上下文管理器处理
                    pass
        else:
            # 其他类型的传输可以在这里添加
            raise ValueError(
                f"Unsupported server type for streaming: {self.server.type.value}"
            )

    async def _create_transport(self) -> None:
        """创建底层传输"""
        try:
            # 创建自定义的异步上下文管理器
            self._transport = self._create_client_session()

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
