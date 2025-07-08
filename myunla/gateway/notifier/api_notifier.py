"""API 通知器实现"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from api.mcp import Mcp
from myunla.config.notifier_config import NotifierAPIConfig
from myunla.gateway.notifier.enums import NotifierRole
from myunla.gateway.notifier.notifier import Notifier, NotifierError
from myunla.utils import get_logger

logger = get_logger(__name__)


class APINotifier(Notifier):
    """API 通知器实现"""

    def __init__(
        self, config: NotifierAPIConfig, role: NotifierRole = NotifierRole.BOTH
    ):
        self.config = config
        self.role = role
        self.watchers: set[asyncio.Queue[Optional[Mcp]]] = set()
        self._lock = asyncio.Lock()
        self.app: Optional[FastAPI] = None
        self.server_task: Optional[asyncio.Task] = None
        self._running = False
        self._closed = False

    async def _setup_app(self):
        """设置 FastAPI 应用"""
        if not self.can_receive():
            return

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            logger.info("API 通知器服务启动", extra={"port": self.config.port})
            yield
            logger.info("API 通知器服务关闭")

        self.app = FastAPI(lifespan=lifespan)

        @self.app.post("/_reload")
        async def reload_endpoint(request: Request):
            """接收配置更新的端点"""
            mcp_config: Optional[Mcp] = None

            # 检查是否有请求体
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > 0:
                try:
                    body = await request.json()
                    mcp_config = Mcp(**body)
                    logger.info(
                        "接收到配置更新", extra={"config_name": mcp_config.name}
                    )
                except Exception as e:
                    logger.error(f"解析请求体失败: {e}")
                    raise HTTPException(
                        status_code=400, detail=f"Invalid request body: {e}"
                    )
            else:
                logger.info("接收到重载信号（无配置数据）")

            # 通知所有监听器
            async with self._lock:
                if self.watchers:
                    for queue in self.watchers.copy():
                        try:
                            queue.put_nowait(mcp_config)
                        except asyncio.QueueFull:
                            logger.warning("监听器队列已满，跳过通知")

            return JSONResponse(
                content={"status": "success", "message": "Reload triggered"}
            )

    async def _start_server(self):
        """启动 HTTP 服务器"""
        if not self.can_receive() or self._running:
            return

        await self._setup_app()
        if self.app is None:
            return

        config = uvicorn.Config(
            app=self.app,
            host="127.0.0.1",  # 只绑定到本地接口，更安全
            port=self.config.port,
            log_level="info",
        )
        server = uvicorn.Server(config)

        try:
            self._running = True
            await server.serve()
        except Exception as e:
            logger.error(f"HTTP 服务器启动失败: {e}")
            raise NotifierError(f"failed to start API server: {e}", cause=e)

    async def watch(self) -> asyncio.Queue[Optional[Mcp]]:
        """监听配置更新"""
        if not self.can_receive():
            raise NotifierError("notifier is not configured to receive updates")

        async with self._lock:
            queue: asyncio.Queue[Optional[Mcp]] = asyncio.Queue(maxsize=10)
            self.watchers.add(queue)

            # 如果服务器还没启动，启动它
            if not self._running and self.server_task is None:
                self.server_task = asyncio.create_task(self._start_server())

        return queue

    async def notify_update(self, updated: Optional[Mcp]) -> None:
        """发送配置更新通知"""
        if not self.can_send():
            raise NotifierError("notifier is not configured to send updates")

        if not self.config.target_url:
            raise NotifierError("target URL is not configured")

        # 构建重载 URL
        reload_url = self.config.target_url
        if not reload_url.endswith("/_reload"):
            if not reload_url.endswith("/"):
                reload_url += "/"
            reload_url += "_reload"

        try:
            async with httpx.AsyncClient() as client:
                if updated is None:
                    # 发送不带配置的重载信号
                    response = await client.post(reload_url)
                    await self._handle_response(response)
                else:
                    # 发送带配置的更新
                    payload = updated.model_dump_json()
                    headers = {"Content-Type": "application/json"}

                    response = await client.post(
                        reload_url, content=payload, headers=headers
                    )
                    await self._handle_response(response)

                logger.info(
                    "发送 API 配置更新通知",
                    extra={
                        "target_url": reload_url,
                        "config_name": (
                            updated.name if updated else "reload_signal"
                        ),
                    },
                )

        except Exception as e:
            logger.error(f"发送 API 通知失败: {e}")
            raise NotifierError(
                f"failed to send API notification: {e}", cause=e
            )

    async def _handle_response(self, response: httpx.Response):
        """处理 HTTP 响应"""
        if response.status_code != 200:
            body = response.text
            raise NotifierError(
                f"unexpected status code: {response.status_code}, body: {body}"
            )

    async def _remove_watcher(self, queue: asyncio.Queue[Optional[Mcp]]):
        """移除监听器"""
        async with self._lock:
            self.watchers.discard(queue)

    def can_receive(self) -> bool:
        """返回是否可以接收更新"""
        return self.role in (NotifierRole.RECEIVER, NotifierRole.BOTH)

    def can_send(self) -> bool:
        """返回是否可以发送更新"""
        return self.role in (NotifierRole.SENDER, NotifierRole.BOTH)

    async def close(self):
        """关闭通知器"""
        self._closed = True

        # 关闭所有监听器队列
        async with self._lock:
            for queue in self.watchers.copy():
                try:
                    # 发送关闭信号
                    queue.put_nowait(None)
                except asyncio.QueueFull:
                    pass
            self.watchers.clear()

        # 停止服务器任务
        if self.server_task and not self.server_task.done():
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass

        self._running = False
        logger.info("API 通知器已关闭")

    @property
    def is_closed(self) -> bool:
        """检查是否已关闭"""
        return self._closed

    @property
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running


def create_api_notifier(
    port: int = 8080,
    role: NotifierRole = NotifierRole.BOTH,
    target_url: str = "",
) -> APINotifier:
    """创建 API 通知器实例"""
    config = NotifierAPIConfig(
        port=port,
        target_url=target_url,
    )
    return APINotifier(config, role)
