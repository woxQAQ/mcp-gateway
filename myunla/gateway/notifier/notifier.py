"""配置更新通知器接口定义"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional

from api.mcp import Mcp


class Notifier(ABC):
    """
    配置更新通知器抽象接口

    定义了MCP配置更新通知的标准接口，用于在配置发生变化时
    通知相关的服务组件进行重载或更新操作。

    通知器支持双向通信：
    - 可以监听配置更新（watch方法）
    - 可以发送配置更新通知（notify_update方法）

    使用场景：
    - 微服务配置热更新
    - 分布式系统配置同步
    - 服务发现与注册

    注意事项：
    - 实现类需要处理网络异常和连接断开
    - 需要确保资源正确释放（调用close方法）
    - 支持优雅关闭和错误恢复
    """

    @abstractmethod
    async def watch(self) -> asyncio.Queue[Optional[Mcp]]:
        """
        返回一个队列，用于接收服务器更新时的通知

        Returns:
            接收MCPConfig更新通知的异步队列

        Raises:
            NotifierError: 监听失败时抛出
        """
        pass

    @abstractmethod
    async def notify_update(self, updated: Optional[Mcp]) -> None:
        """
        触发更新通知

        Args:
            updated: 更新的MCP配置，None表示重载信号

        Raises:
            NotifierError: 通知失败时抛出
        """
        pass

    @abstractmethod
    def can_receive(self) -> bool:
        """
        返回通知器是否可以接收更新

        Returns:
            如果可以接收更新则返回True
        """
        pass

    @abstractmethod
    def can_send(self) -> bool:
        """
        返回通知器是否可以发送更新

        Returns:
            如果可以发送更新则返回True
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        关闭通知器，释放所有资源

        Raises:
            NotifierError: 关闭失败时抛出
        """
        pass


class NotifierError(Exception):
    """
    通知器操作异常

    当通知器在执行监听、发送、关闭等操作时发生错误时抛出此异常。
    异常包含详细的错误信息和可选的根因异常。

    Attributes:
        message: 错误描述信息
        cause: 导致此异常的根因异常（可选）
    """

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause
        super().__init__(message)
