"""信号通知器实现"""

import asyncio
import os
import signal
from pathlib import Path
from typing import Optional

from api.mcp import Mcp
from myunla.gateway.notifier.enums import NotifierRole
from myunla.gateway.notifier.notifier import Notifier, NotifierError
from myunla.utils import get_logger

logger = get_logger(__name__)


class SignalNotifierConfig:
    """信号通知器配置"""

    def __init__(
        self,
        pid_file: str,
        role: NotifierRole = NotifierRole.BOTH,
    ):
        if not pid_file:
            raise ValueError("PID file path is required")
        self.pid_file = pid_file
        self.role = role


class SignalNotifier(Notifier):
    """信号通知器实现"""

    def __init__(self, config: SignalNotifierConfig):
        self.config = config
        self.watchers: set[asyncio.Queue[Optional[Mcp]]] = set()
        self._lock = asyncio.Lock()
        self._signal_handler_task: Optional[asyncio.Task] = None
        self._original_handler = None
        self._running = False
        self._closed = False

    def _setup_signal_handler(self):
        """设置信号处理器"""
        if not self.can_receive():
            return

        def signal_handler(signum, frame):
            """信号处理函数"""
            logger.info(
                "接收到重载信号", extra={"signal": signal.Signals(signum).name}
            )
            # 创建任务来处理异步通知
            asyncio.create_task(self._notify_watchers())

        # 保存原始处理器
        self._original_handler = signal.signal(signal.SIGHUP, signal_handler)
        logger.info("信号处理器已设置", extra={"signal": "SIGHUP"})

    def _restore_signal_handler(self):
        """恢复原始信号处理器"""
        if self._original_handler is not None:
            signal.signal(signal.SIGHUP, self._original_handler)
            self._original_handler = None
            logger.info("信号处理器已恢复")

    async def _notify_watchers(self):
        """通知所有观察者"""
        async with self._lock:
            if not self.watchers:
                return

            for queue in self.watchers.copy():
                try:
                    # 发送 None 表示重载信号（不带配置）
                    queue.put_nowait(None)
                    logger.debug("通知观察者")
                except asyncio.QueueFull:
                    logger.warning("观察者队列已满，跳过通知")

    async def watch(self) -> asyncio.Queue[Optional[Mcp]]:
        """监听信号更新"""
        if not self.can_receive():
            raise NotifierError("notifier is not configured to receive updates")

        async with self._lock:
            queue: asyncio.Queue[Optional[Mcp]] = asyncio.Queue(maxsize=10)
            self.watchers.add(queue)

            # 如果是第一个观察者，设置信号处理器
            if not self._running:
                self._setup_signal_handler()
                self._running = True

        return queue

    async def notify_update(self, updated: Optional[Mcp]) -> None:
        """发送信号通知（忽略配置参数，只发送信号）"""
        if not self.can_send():
            raise NotifierError("notifier is not configured to send updates")

        try:
            await self._send_signal_to_pid_file()
            logger.info("成功发送 SIGHUP 信号")
        except Exception as e:
            logger.error(f"发送信号失败: {e}")
            raise NotifierError(f"failed to send signal: {e}", cause=e)

    async def _send_signal_to_pid_file(self):
        """向 PID 文件中的进程发送信号"""
        pid_path = Path(self.config.pid_file)

        if not pid_path.exists():
            raise NotifierError(f"PID file not found: {self.config.pid_file}")

        try:
            # 读取 PID
            pid_str = pid_path.read_text().strip()
            if not pid_str:
                raise NotifierError(f"Empty PID file: {self.config.pid_file}")

            pid = int(pid_str)

            # 检查进程是否存在
            try:
                os.kill(pid, 0)  # 信号 0 用于检查进程是否存在
            except OSError:
                raise NotifierError(f"Process with PID {pid} not found")

            # 发送 SIGHUP 信号
            os.kill(pid, signal.SIGHUP)
            logger.info(
                "发送信号到进程",
                extra={
                    "pid": pid,
                    "signal": "SIGHUP",
                    "pid_file": self.config.pid_file,
                },
            )

        except ValueError as e:
            raise NotifierError(
                f"Invalid PID in file {self.config.pid_file}: {e}"
            )
        except PermissionError as e:
            raise NotifierError(f"Permission denied sending signal: {e}")
        except Exception as e:
            raise NotifierError(f"Failed to send signal: {e}")

    async def _remove_watcher(self, queue: asyncio.Queue[Optional[Mcp]]):
        """移除观察者"""
        async with self._lock:
            self.watchers.discard(queue)

            # 如果没有观察者了，清理信号处理器
            if not self.watchers and self._running:
                self._restore_signal_handler()
                self._running = False

    def can_receive(self) -> bool:
        """返回是否可以接收更新"""
        return self.config.role in (NotifierRole.RECEIVER, NotifierRole.BOTH)

    def can_send(self) -> bool:
        """返回是否可以发送更新"""
        return self.config.role in (NotifierRole.SENDER, NotifierRole.BOTH)

    async def close(self):
        """关闭通知器"""
        self._closed = True

        # 关闭所有观察者队列
        async with self._lock:
            for queue in self.watchers.copy():
                try:
                    # 发送关闭信号
                    queue.put_nowait(None)
                except asyncio.QueueFull:
                    pass
            self.watchers.clear()

            # 恢复信号处理器
            if self._running:
                self._restore_signal_handler()
                self._running = False

        logger.info("信号通知器已关闭")

    @property
    def is_closed(self) -> bool:
        """检查是否已关闭"""
        return self._closed

    @property
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running


def create_signal_notifier(
    pid_file: str,
    role: NotifierRole = NotifierRole.BOTH,
) -> SignalNotifier:
    """创建信号通知器实例"""
    config = SignalNotifierConfig(
        pid_file=pid_file,
        role=role,
    )
    return SignalNotifier(config)


def write_pid_file(pid_file: str, pid: Optional[int] = None):
    """写入 PID 文件"""
    if pid is None:
        pid = os.getpid()

    pid_path = Path(pid_file)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(str(pid))
    logger.info("写入 PID 文件", extra={"pid": pid, "file": pid_file})


def remove_pid_file(pid_file: str):
    """删除 PID 文件"""
    pid_path = Path(pid_file)
    if pid_path.exists():
        pid_path.unlink()
        logger.info("删除 PID 文件", extra={"file": pid_file})
