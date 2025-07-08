"""Redis 通知器实现"""

import asyncio
import json
from typing import TYPE_CHECKING, Optional

import redis.asyncio as redis
from redis.asyncio.sentinel import Sentinel

from api.mcp import Mcp
from myunla.config.notifier_config import NotifierRedisConfig
from myunla.config.session_config import RedisClusterType
from myunla.gateway.notifier.enums import NotifierRole
from myunla.gateway.notifier.notifier import Notifier, NotifierError
from myunla.utils import get_logger
from myunla.utils.redis_utils import split_by_multiple_delimiters

if TYPE_CHECKING:
    from redis.asyncio.client import Redis

logger = get_logger(__name__)


class RedisNotifier(Notifier):
    """Redis 通知器实现"""

    def __init__(
        self,
        config: NotifierRedisConfig,
        role: NotifierRole = NotifierRole.BOTH,
    ):
        self.config = config
        self.role = role
        self.client: Optional[Redis] = None
        self.pubsub = None
        self._listen_task: Optional[asyncio.Task] = None
        self._connected = False
        self._queue: Optional[asyncio.Queue[Optional[Mcp]]] = None
        self._closed = False

    async def _create_redis_client(self):
        """创建 Redis 客户端"""
        addrs = split_by_multiple_delimiters(self.config.addr, ";", ",")

        try:
            if self.config.cluster_type == RedisClusterType.SENTINEL:
                # 哨兵模式
                sentinel = Sentinel(
                    [
                        (addr.split(":")[0], int(addr.split(":")[1]))
                        for addr in addrs
                    ]
                )
                client = sentinel.master_for(
                    self.config.master_name,
                    username=self.config.username,
                    password=self.config.password,
                    db=self.config.db,
                )
            else:
                # 单机模式
                addr = addrs[0]
                host, port = addr.split(":")
                client = redis.Redis(
                    host=host,
                    port=int(port),
                    username=self.config.username,
                    password=self.config.password,
                    db=self.config.db,
                    decode_responses=False,
                )

            # 测试连接
            await client.ping()
            logger.info("Redis 连接成功", extra={"addr": self.config.addr})
            return client

        except Exception as e:
            logger.error(
                f"Redis 连接失败: {e}", extra={"addr": self.config.addr}
            )
            raise NotifierError(f"failed to connect to Redis: {e}", cause=e)

    async def _start_watching(self):
        """开始监听 Redis 发布订阅"""
        if not self.can_receive():
            return

        if self.client is None:
            self.client = await self._create_redis_client()

        try:
            self.pubsub = self.client.pubsub()
            await self.pubsub.subscribe(self.config.topic)
            self._listen_task = asyncio.create_task(self._handle_messages())
            self._connected = True
            logger.info(
                "开始监听 Redis 发布订阅", extra={"topic": self.config.topic}
            )
        except Exception as e:
            logger.error(f"启动 Redis 监听失败: {e}")
            raise NotifierError(
                f"failed to start Redis listening: {e}", cause=e
            )

    async def _handle_messages(self):
        """处理 Redis 消息"""
        if self.pubsub is None:
            return

        try:
            async for message in self.pubsub.listen():
                if message["type"] != "message":
                    continue

                try:
                    payload = message["data"]
                    if isinstance(payload, bytes):
                        payload = payload.decode("utf-8")

                    if payload.strip() == "":
                        # 空消息表示重载信号
                        mcp_config = None
                        config_name = "reload_signal"
                    else:
                        # 解析MCP配置
                        mcp_data = json.loads(payload)
                        mcp_config = Mcp(**mcp_data)
                        config_name = mcp_config.name

                    if self._queue is not None:
                        try:
                            self._queue.put_nowait(mcp_config)
                            logger.debug(
                                "接收到 MCP 配置更新",
                                extra={"name": config_name},
                            )
                        except asyncio.QueueFull:
                            logger.warning(
                                "通知队列已满，丢弃消息",
                                extra={"name": config_name},
                            )

                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    logger.warning(f"解析 Redis 消息失败: {e}")
                except Exception as e:
                    logger.error(f"处理 Redis 消息失败: {e}")

        except asyncio.CancelledError:
            logger.info("Redis 消息监听任务已取消")
        except Exception as e:
            logger.error(f"Redis 消息监听异常: {e}")

    async def watch(self) -> asyncio.Queue[Optional[Mcp]]:
        """监听配置更新"""
        if not self.can_receive():
            raise NotifierError("notifier is not configured to receive updates")

        if self._queue is None:
            self._queue = asyncio.Queue()

        if not self._connected:
            await self._start_watching()

        return self._queue

    async def notify_update(self, updated: Optional[Mcp]) -> None:
        """发送配置更新通知"""
        if not self.can_send():
            raise NotifierError("notifier is not configured to send updates")

        if self.client is None:
            self.client = await self._create_redis_client()

        try:
            if updated is None:
                # 发送重载信号
                payload = ""
                config_name = "reload_signal"
                tenant_name = ""
            else:
                # 序列化 MCP 配置
                payload = updated.model_dump_json()
                config_name = updated.name
                tenant_name = updated.tenant_name

            # 发布到 Redis
            await self.client.publish(self.config.topic, payload)

            logger.info(
                "发送 MCP 配置更新通知",
                extra={
                    "name": config_name,
                    "tenant": tenant_name,
                    "topic": self.config.topic,
                },
            )

        except Exception as e:
            logger.error(f"发送配置更新通知失败: {e}")
            raise NotifierError(
                f"failed to publish update notification: {e}", cause=e
            )

    def can_receive(self) -> bool:
        """返回是否可以接收更新"""
        return self.role in (NotifierRole.RECEIVER, NotifierRole.BOTH)

    def can_send(self) -> bool:
        """返回是否可以发送更新"""
        return self.role in (NotifierRole.SENDER, NotifierRole.BOTH)

    async def close(self):
        """关闭通知器"""
        self._closed = True

        # 停止监听任务
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        # 关闭发布订阅
        if self.pubsub:
            try:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()
            except Exception as e:
                logger.warning(f"关闭 Redis 发布订阅失败: {e}")

        # 关闭Redis连接
        if self.client:
            try:
                await self.client.close()
            except Exception as e:
                logger.warning(f"关闭 Redis 连接失败: {e}")

        self._connected = False
        logger.info("Redis 通知器已关闭")

    @property
    def is_closed(self) -> bool:
        """检查是否已关闭"""
        return self._closed

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected


def create_redis_notifier(
    addr: str,
    cluster_type: str = RedisClusterType.SINGLE,
    master_name: str = "",
    username: str = "",
    password: Optional[str] = None,
    db: int = 0,
    topic: str = "mcp_config_updates",
    role: NotifierRole = NotifierRole.BOTH,
) -> RedisNotifier:
    """创建 Redis 通知器实例"""
    config = NotifierRedisConfig(
        addr=addr,
        username=username,
        password=password,
        db=db,
        cluster_type=cluster_type,
        master_name=master_name,
        topic=topic,
    )
    return RedisNotifier(config, role)
