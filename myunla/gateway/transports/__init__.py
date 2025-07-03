from typing import Optional

from mcp import Tool
from mcp.types import CallToolRequestParams

from api.mcp import Mcp, McpServer
from myunla.gateway.transports.base import Transport
from myunla.gateway.transports.sse import SSETransport
from myunla.gateway.transports.stdio import STDIOTransport
from myunla.gateway.transports.streamable import (
    StreamableTransport,
)
from myunla.templates.context import Context, RequestWrapper
from myunla.utils.logger import get_logger

logger = get_logger(__name__)


class TransportManager:
    """管理多个 Transport 实例的管理器"""

    def __init__(self, config: Mcp):
        self.config = config
        self._transports: dict[str, Transport] = {}
        self._is_running = False

    async def start(self, context: Context) -> None:
        """启动所有传输"""
        if self._is_running:
            logger.warning("TransportManager already running")
            return

        try:
            # 为每个服务器创建对应的 Transport
            await self._create_transports()

            # 启动所有 Transport
            for server_name, transport in self._transports.items():
                try:
                    await transport.start(context)
                    logger.info(f"Started transport for server: {server_name}")
                except Exception as e:
                    logger.error(
                        f"Failed to start transport for server {server_name}: {e}"
                    )
                    raise

            self._is_running = True
            logger.info("TransportManager started successfully")

        except Exception as e:
            logger.error(f"Failed to start TransportManager: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """停止所有传输"""
        if not self._is_running:
            return

        # 停止所有 Transport
        for server_name, transport in self._transports.items():
            try:
                await transport.stop()
                logger.info(f"Stopped transport for server: {server_name}")
            except Exception as e:
                logger.error(
                    f"Error stopping transport for server {server_name}: {e}"
                )

        self._transports.clear()
        self._is_running = False
        logger.info("TransportManager stopped")

    async def fetch_all_tools(self) -> list[Tool]:
        """从所有传输获取工具列表"""
        if not self._is_running:
            raise RuntimeError("TransportManager is not running")

        all_tools = []

        for server_name, transport in self._transports.items():
            try:
                tools = await transport.fetch_tools()
                all_tools.extend(tools)
                logger.info(
                    f"Fetched {len(tools)} tools from server: {server_name}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to fetch tools from server {server_name}: {e}"
                )

        return all_tools

    async def call_tool(
        self, call_tool_params: CallToolRequestParams, req: RequestWrapper
    ):
        """调用工具"""
        if not self._is_running:
            raise RuntimeError("TransportManager is not running")

        tool_name = call_tool_params.name
        transport = await self._find_transport_for_tool(tool_name)

        if not transport:
            raise ValueError(f"No transport found for tool: {tool_name}")

        return await transport.call_tools(call_tool_params, req)

    def get_transport_for_server(self, server_name: str) -> Optional[Transport]:
        """获取指定服务器的传输"""
        return self._transports.get(server_name)

    async def _create_transports(self) -> None:
        """为所有服务器创建对应的 Transport"""
        for server in self.config.servers:
            try:
                transport = self._create_transport_for_server(server)
                self._transports[server.name] = transport
                logger.info(
                    f"Created {server.type.value} transport for server: {server.name}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to create transport for server {server.name}: {e}"
                )
                raise

    def _create_transport_for_server(self, server: McpServer) -> Transport:
        """根据服务器类型创建对应的 Transport"""
        if server.type.value == "sse":
            return SSETransport(server)
        elif server.type.value == "stdio":
            return STDIOTransport(server)
        else:
            raise ValueError(f"Unsupported server type: {server.type.value}")

    def _create_streamable_transport_for_server(
        self, server: McpServer
    ) -> StreamableTransport:
        """根据服务器类型创建对应的流式 Transport"""
        # 目前只支持 SSE 的流式传输
        if server.type.value == "sse":
            return StreamableTransport(server)
        else:
            raise ValueError(
                f"Streaming not supported for server type: {server.type.value}"
            )

    async def _find_transport_for_tool(
        self, tool_name: str
    ) -> Optional[Transport]:
        """查找包含指定工具的传输"""
        for transport in self._transports.values():
            try:
                # 获取该传输的工具列表
                tools = await transport.fetch_tools()
                for tool in tools:
                    if tool.name == tool_name:
                        return transport
            except Exception as e:
                logger.error(f"Error checking tools in transport: {e}")
                continue

        return None
