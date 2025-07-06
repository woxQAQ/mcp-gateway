"""Transport工厂函数"""

from api.mcp import McpServer
from myunla.gateway.transports.base import Transport
from myunla.gateway.transports.sse import SSETransport
from myunla.gateway.transports.stdio import StdIOTransport


def create_transport(server: McpServer) -> Transport:
    """
    根据服务器类型创建对应的Transport

    Args:
        server: MCP服务器配置

    Returns:
        对应类型的Transport实例

    Raises:
        ValueError: 不支持的服务器类型
    """
    if server.type.value == "sse":
        return SSETransport(server)
    elif server.type.value == "stdio":
        return StdIOTransport(server)
    else:
        raise ValueError(f"Unsupported server type: {server.type.value}")


__all__ = [
    "create_transport",
    "SSETransport",
    "StdIOTransport",
]
