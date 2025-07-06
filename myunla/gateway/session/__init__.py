"""Session management module for gateway."""

from .memory import MemoryConnection, MemoryStore
from .session import (
    Connection,
    Message,
    Meta,
    RequestInfo,
    SessionNotFoundError,
    Store,
)

# Redis imports - 可选依赖
try:
    from .redis import RedisConnection, RedisStore, create_redis_store

    _redis_available = True
except ImportError:
    _redis_available = False
    RedisConnection = None
    RedisStore = None
    create_redis_store = None

__all__ = [
    "Store",
    "Connection",
    "Meta",
    "Message",
    "RequestInfo",
    "SessionNotFoundError",
    "MemoryStore",
    "MemoryConnection",
]

# 只有在Redis可用时才导出Redis相关类
if _redis_available:
    __all__.extend(["RedisStore", "RedisConnection", "create_redis_store"])
