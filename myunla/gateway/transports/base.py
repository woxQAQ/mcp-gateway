import asyncio
from abc import ABC
from collections.abc import Callable
from typing import Any, Optional

from mcp import Tool
from mcp.types import CallToolRequestParams, CallToolResult

from api.mcp import McpServer
from myunla.templates.context import Context, RequestWrapper


class Transport(ABC):
    def __init__(self, server: McpServer):
        self.server = server
        self._lock = asyncio.Lock()

    async def start(self, context: Optional[Context] = None):
        """
        Start the transport.
        """
        pass

    async def stop(self):
        """
        Stop the transport.
        """
        pass

    async def fetch_tools(self) -> list[Tool]:  # type: ignore
        """
        Fetch tools from the transport.
        """
        pass

    async def call_tools(
        self, call_tool_params: CallToolRequestParams, req: RequestWrapper
    ) -> CallToolResult:  # type: ignore
        """
        Call a tool.
        """
        pass


def transport_has_started(func: Callable[..., Any]) -> Callable[..., Any]:
    """装饰器：确保 transport 在调用前已启动"""

    async def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        if not self._transport:
            await self.start()

        if not self._transport:
            raise RuntimeError(
                f"No transport available for server: {self.server.name}"
            )

        return await func(self, *args, **kwargs)

    return wrapper
