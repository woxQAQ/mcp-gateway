"""组合通知器实现"""

import asyncio
from typing import Optional

from api.mcp import Mcp
from myunla.gateway.notifier.notifier import (
    Notifier,
    NotifierError,
)
from myunla.utils import get_logger

logger = get_logger(__name__)


class CompositeNotifier(Notifier):
    """组合通知器实现，可以组合多个通知器"""

    def __init__(self, notifiers: list[Notifier]):
        super().__init__()
        self.notifiers = notifiers or []
        self.watchers: set[asyncio.Queue[Optional[Mcp]]] = set()
        self._lock = asyncio.Lock()
        self._watch_tasks: list[asyncio.Task] = []
        self._running = False
        self._is_closed = False

    async def _start_watching_underlying_notifiers(self):
        """开始监听所有底层通知器"""
        if self._running:
            return

        for notifier in self.notifiers:
            if not notifier.can_receive():
                continue

            try:
                # 启动监听底层通知器
                task = asyncio.create_task(
                    self._watch_underlying_notifier(notifier)
                )
                self._watch_tasks.append(task)

                logger.debug(
                    "开始监听底层通知器",
                    extra={"notifier_type": type(notifier).__name__},
                )
            except Exception as e:
                logger.error(
                    f"启动底层通知器监听失败: {e}",
                    extra={"notifier_type": type(notifier).__name__},
                )

        self._running = True

    async def _watch_underlying_notifier(self, notifier: Notifier):
        """监听单个底层通知器"""
        try:
            queue = await notifier.watch()

            while not self._is_closed:
                try:
                    # 等待底层通知器的更新
                    config = await queue.get()

                    # 转发给所有观察者
                    await self._notify_watchers(config)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(
                        f"处理底层通知器消息失败: {e}",
                        extra={"notifier_type": type(notifier).__name__},
                    )

        except Exception as e:
            logger.error(
                f"监听底层通知器失败: {e}",
                extra={"notifier_type": type(notifier).__name__},
            )

    async def _notify_watchers(self, config: Optional[Mcp]):
        """通知所有观察者"""
        async with self._lock:
            if not self.watchers:
                return

            for queue in self.watchers.copy():
                try:
                    queue.put_nowait(config)
                    logger.debug(
                        "转发通知给观察者",
                        extra={
                            "config_name": (
                                config.name if config else "reload_signal"
                            )
                        },
                    )
                except asyncio.QueueFull:
                    logger.warning(
                        "观察者队列已满，跳过通知",
                        extra={
                            "config_name": (
                                config.name if config else "reload_signal"
                            )
                        },
                    )

    async def watch(self) -> asyncio.Queue[Optional[Mcp]]:
        """监听配置更新"""
        if not self.can_receive():
            raise NotifierError("notifier is not configured to receive updates")

        async with self._lock:
            queue: asyncio.Queue[Optional[Mcp]] = asyncio.Queue(maxsize=10)
            self.watchers.add(queue)

            # 如果是第一个观察者，开始监听底层通知器
            if len(self.watchers) == 1 and not self._running:
                await self._start_watching_underlying_notifiers()

        return queue

    async def notify_update(self, updated: Optional[Mcp]) -> None:
        """发送配置更新通知到所有能发送的底层通知器"""
        if not self.can_send():
            raise NotifierError("notifier is not configured to send updates")

        last_error = None
        success_count = 0

        for notifier in self.notifiers:
            if not notifier.can_send():
                continue

            try:
                await notifier.notify_update(updated)
                success_count += 1
                logger.debug(
                    "成功发送通知到底层通知器",
                    extra={"notifier_type": type(notifier).__name__},
                )
            except Exception as e:
                last_error = e
                logger.error(
                    f"发送通知到底层通知器失败: {e}",
                    extra={"notifier_type": type(notifier).__name__},
                )

        if success_count == 0 and last_error:
            # 如果所有发送都失败了，抛出最后一个错误
            raise NotifierError(
                f"all underlying notifiers failed: {last_error}",
                cause=last_error,
            )

        if last_error:
            logger.warning(
                f"部分底层通知器发送失败，但至少有 {success_count} 个成功"
            )

    def can_receive(self) -> bool:
        """如果任何底层通知器可以接收，则返回 True"""
        return any(notifier.can_receive() for notifier in self.notifiers)

    def can_send(self) -> bool:
        """如果任何底层通知器可以发送，则返回 True"""
        return any(notifier.can_send() for notifier in self.notifiers)

    async def close(self):
        """关闭组合通知器"""
        await super().close()

        # 取消所有监听任务
        for task in self._watch_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._watch_tasks.clear()

        # 关闭所有观察者队列
        async with self._lock:
            for queue in self.watchers.copy():
                try:
                    # 发送关闭信号
                    queue.put_nowait(None)
                except asyncio.QueueFull:
                    pass
            self.watchers.clear()

        # 关闭所有底层通知器
        for notifier in self.notifiers:
            try:
                await notifier.close()
            except Exception as e:
                logger.error(
                    f"关闭底层通知器失败: {e}",
                    extra={"notifier_type": type(notifier).__name__},
                )

        self._running = False
        logger.info("组合通知器已关闭")

    @property
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running

    def add_notifier(self, notifier: Notifier):
        """添加新的底层通知器"""
        if notifier not in self.notifiers:
            self.notifiers.append(notifier)
            logger.info(
                "添加底层通知器",
                extra={"notifier_type": type(notifier).__name__},
            )

            # 如果正在运行且新通知器可以接收，启动监听
            if self._running and notifier.can_receive():
                task = asyncio.create_task(
                    self._watch_underlying_notifier(notifier)
                )
                self._watch_tasks.append(task)

    def remove_notifier(self, notifier: Notifier):
        """移除底层通知器"""
        if notifier in self.notifiers:
            self.notifiers.remove(notifier)
            logger.info(
                "移除底层通知器",
                extra={"notifier_type": type(notifier).__name__},
            )

    def get_notifiers(self) -> list[Notifier]:
        """获取所有底层通知器"""
        return self.notifiers.copy()

    def get_notifier_count(self) -> int:
        """获取底层通知器数量"""
        return len(self.notifiers)

    def get_receiver_count(self) -> int:
        """获取可接收的底层通知器数量"""
        return sum(1 for notifier in self.notifiers if notifier.can_receive())

    def get_sender_count(self) -> int:
        """获取可发送的底层通知器数量"""
        return sum(1 for notifier in self.notifiers if notifier.can_send())


def create_composite_notifier(*notifiers: Notifier) -> CompositeNotifier:
    """创建组合通知器实例"""
    return CompositeNotifier(list(notifiers))
