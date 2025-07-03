from .auth import AsyncUserRepository
from .mcp import AsyncMcpConfigRepository


class AsyncDBOps(
    AsyncUserRepository,
    AsyncMcpConfigRepository,
):
    def __init__(self, session=None):
        super().__init__(session)


async_db_ops = AsyncDBOps()

__all__ = ["async_db_ops"]
