from abc import ABC, abstractmethod
from asyncio import Queue
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from myunla.config import SessionConfig


class Message(BaseModel):
    event: str
    data: bytes


class RequestInfo(BaseModel):
    headers: dict[str, str]
    queries: dict[str, str]
    cookies: dict[str, str]


class Meta(BaseModel):
    id: str
    created_at: datetime
    prefix: str
    type: str
    request: RequestInfo
    extra: Optional[dict] = None


class Connection(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def event_queue(self) -> Queue[Message]:
        """返回事件队列"""
        pass

    @abstractmethod
    async def send(self, message: Message):
        """发送消息"""
        pass

    @abstractmethod
    async def close(self):
        """关闭连接"""
        pass

    @abstractmethod
    def meta(self) -> Meta:
        """返回连接元数据"""
        pass


class Store(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    async def register(self, meta: Meta) -> Connection:
        """注册新连接"""
        pass

    @abstractmethod
    async def unregister(self, id: str):
        """注销连接"""
        pass

    @abstractmethod
    async def get(self, id: str) -> Connection:
        """获取连接"""
        pass

    @abstractmethod
    async def list(self) -> list[Connection]:
        """列出所有连接"""
        pass


class SessionNotFoundError(Exception):
    """会话未找到异常"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"session not found: {session_id}")


def create_store(config: SessionConfig) -> Store:
    if config.store == "memory":
        from myunla.gateway.session.memory import MemoryStore

        return MemoryStore()
    elif config.store == "redis":
        from myunla.gateway.session.redis import RedisStore

        return RedisStore(config.redis_config)
    else:
        raise ValueError(f"invalid store type: {config.store}")
