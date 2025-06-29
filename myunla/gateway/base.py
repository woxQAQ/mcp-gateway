import asyncio
from abc import ABC

from api.mcp import Mcp


class Transport(ABC):
    def __init__(self, config: Mcp):
        self.config = config
        self.is_running = False
        self._lock = asyncio.Lock()

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def start(self):
        """
        Start the transport.
        """
        pass

    async def stop(self):
        """
        Stop the transport.
        """
        pass

    async def fetch_tools(self):
        """
        Fetch tools from the transport.
        """
        pass
