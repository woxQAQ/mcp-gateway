import asyncio

from myunla.gateway.session.session import (
    Connection,
    Message,
    Meta,
    SessionNotFoundError,
    Store,
)
from myunla.utils import get_logger

try:
    from aiorwlock import RWLock

    HAS_RWLOCK = True
except ImportError:
    HAS_RWLOCK = False

logger = get_logger(__name__)


class MemoryConnection(Connection):
    """内存连接实现"""

    def __init__(self, meta: Meta):
        self._meta = meta
        self._queue: asyncio.Queue[Message] = asyncio.Queue(maxsize=100)
        self._closed = False

    def event_queue(self) -> asyncio.Queue[Message]:
        """返回事件队列"""
        return self._queue

    async def send(self, message: Message):
        """发送消息到队列"""
        if self._closed:
            raise RuntimeError("Connection is closed")

        try:
            self._queue.put_nowait(message)
        except asyncio.QueueFull:
            raise RuntimeError("message queue is full")

    async def close(self):
        """关闭连接"""
        if not self._closed:
            self._closed = True
            # 清空队列并关闭
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except asyncio.QueueEmpty:
                    break

    def meta(self) -> Meta:
        """返回连接元数据"""
        return self._meta


class MemoryStore(Store):
    """内存会话存储实现"""

    def __init__(self):
        super().__init__()
        self._lock = RWLock() if HAS_RWLOCK else asyncio.Lock()
        self._conns: dict[str, Connection] = {}

    async def register(self, meta: Meta) -> Connection:
        """注册新连接"""
        if HAS_RWLOCK:
            async with self._lock.writer:
                # 检查连接是否已存在
                if meta.id in self._conns:
                    raise ValueError(f"connection already exists: {meta.id}")

                # 创建新连接
                conn = MemoryConnection(meta)

                # 存储连接
                self._conns[meta.id] = conn

                return conn
        else:
            async with self._lock:
                # 检查连接是否已存在
                if meta.id in self._conns:
                    raise ValueError(f"connection already exists: {meta.id}")

                # 创建新连接
                conn = MemoryConnection(meta)

                # 存储连接
                self._conns[meta.id] = conn

                return conn

    async def get(self, id: str) -> Connection:
        """获取连接"""
        if HAS_RWLOCK:
            async with self._lock.reader:
                conn = self._conns.get(id)
        else:
            async with self._lock:
                conn = self._conns.get(id)

        if conn is None:
            raise SessionNotFoundError(id)
        return conn

    async def unregister(self, id: str):
        """注销连接"""
        if HAS_RWLOCK:
            async with self._lock.writer:
                conn = self._conns.get(id)
                if conn is None:
                    raise SessionNotFoundError(id)

                # 关闭连接
                try:
                    await conn.close()
                except Exception as e:
                    logger.error(
                        "failed to close connection",
                        extra={"id": id, "error": str(e)},
                    )

                # 删除连接
                del self._conns[id]
        else:
            async with self._lock:
                conn = self._conns.get(id)
                if conn is None:
                    raise SessionNotFoundError(id)

                # 关闭连接
                try:
                    await conn.close()
                except Exception as e:
                    logger.error(
                        "failed to close connection",
                        extra={"id": id, "error": str(e)},
                    )

                # 删除连接
                del self._conns[id]

    async def list(self) -> list[Connection]:
        """列出所有连接"""
        if HAS_RWLOCK:
            async with self._lock.reader:
                conns = list(self._conns.values())
        else:
            async with self._lock:
                conns = list(self._conns.values())

        return conns
