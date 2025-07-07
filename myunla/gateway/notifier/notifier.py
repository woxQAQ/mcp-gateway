"""配置更新通知器接口定义"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional

from api.mcp import Mcp


class Notifier(ABC):
    """配置更新通知器接口"""

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
    """通知器异常"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause
        super().__init__(message)


class BaseNotifier(Notifier):
    """通知器基类，提供默认实现"""

    def __init__(self):
        self._queue: Optional[asyncio.Queue[Optional[Mcp]]] = None
        self._closed = False

    async def watch(self) -> asyncio.Queue[Optional[Mcp]]:
        """返回监听队列"""
        if self._queue is None:
            self._queue = asyncio.Queue()
        return self._queue

    async def close(self):
        """关闭通知器"""
        self._closed = True
        if self._queue is not None:
            # 清空队列
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except asyncio.QueueEmpty:
                    break

    @property
    def is_closed(self) -> bool:
        """检查是否已关闭"""
        return self._closed
