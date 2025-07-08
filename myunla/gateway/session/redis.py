"""Redis会话存储实现"""

import asyncio
import json
from datetime import datetime
from typing import Optional

from redis.asyncio.client import PubSub, Redis

from myunla.config.session_config import SessionRedisConfig
from myunla.gateway.session.session import (
    Connection,
    Message,
    Meta,
    RequestInfo,
    SessionNotFoundError,
    Store,
)
from myunla.utils import get_logger

logger = get_logger(__name__)


class RedisConnection(Connection):
    """Redis连接实现"""

    def __init__(self, store: 'RedisStore', meta: Meta):
        self.store = store
        self._meta = meta
        self._queue: asyncio.Queue[Message] = asyncio.Queue(maxsize=100)
        self._closed = False

    def event_queue(self) -> asyncio.Queue[Message]:
        """返回事件队列"""
        return self._queue

    async def send(self, message: Message):
        """发送消息"""
        if self._closed:
            raise RuntimeError("Connection is closed")

        # 续期会话TTL
        await self._renew_ttl()

        # 发布事件
        return await self.store._publish_update("event", self._meta, message)

    async def close(self):
        """关闭连接"""
        if not self._closed:
            self._closed = True
            await self.store.unregister(self._meta.id)

    def meta(self) -> Meta:
        """返回连接元数据"""
        return self._meta

    async def _renew_ttl(self):
        """续期会话TTL"""
        if not self.store.client:
            return

        key = self.store._get_session_key(self._meta.id)
        ids_key = self.store._get_ids_key()

        try:
            # 续期会话数据
            await self.store.client.expire(key, self.store.ttl)
            # 续期会话ID集合
            await self.store.client.expire(ids_key, self.store.ttl)
        except Exception as e:
            logger.warning(
                "failed to renew session TTL",
                extra={"id": self._meta.id, "error": str(e)},
            )


class RedisStore(Store):
    """Redis会话存储实现"""

    def __init__(
        self,
        config: SessionRedisConfig,
    ):
        super().__init__()
        self.config = config
        self.client: Redis = Redis(
            host=config.host,
            port=config.port,
            username=config.username,
            password=config.password,
            db=config.db,
        )
        self.pubsub: Optional[PubSub] = None
        self.connections: dict[str, RedisConnection] = {}
        self._lock = asyncio.Lock()
        self._listen_task: Optional[asyncio.Task] = None

        # 配置参数
        self.prefix = config.prefix + ":" if config.prefix else "session:"
        self.topic = config.topic
        self.ttl = int(config.ttl.total_seconds())

    async def initialize(self):
        """初始化Redis连接"""
        try:
            # 单机模式
            self.client = Redis(
                host=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                db=self.config.db,
                decode_responses=False,
            )

            # 测试连接
            await self.client.ping()
            logger.info("Redis连接成功")

            # 订阅会话更新
            self.pubsub = self.client.pubsub()
            await self.pubsub.subscribe(self.topic)

            # 启动监听任务
            self._listen_task = asyncio.create_task(self._handle_updates())

        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise

    async def close(self):
        """关闭Redis连接"""
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        if self.pubsub:
            await self.pubsub.close()

        if self.client:
            await self.client.close()

    async def _handle_updates(self):
        """处理会话更新通知"""
        if not self.pubsub:
            return
        try:
            async for message in self.pubsub.listen():
                if message["type"] != "message":
                    continue

                try:
                    payload = message["data"]
                    if isinstance(payload, bytes):
                        payload = payload.decode("utf-8")

                    update = json.loads(payload)
                    action = update.get("action")
                    meta_data = update.get("meta")
                    message_data = update.get("message")

                    if action == "event" and meta_data and message_data:
                        # 处理事件消息
                        session_id = meta_data.get("id")
                        async with self._lock:
                            conn = self.connections.get(session_id)

                        if conn:
                            try:
                                event_message = Message(
                                    event=message_data["event"],
                                    data=message_data["data"],
                                )
                                conn._queue.put_nowait(event_message)
                                logger.info(
                                    "sent message to connection queue",
                                    extra={
                                        "id": session_id,
                                        "event": event_message.event,
                                    },
                                )
                            except asyncio.QueueFull:
                                logger.warning(
                                    "connection queue is full, dropping message",
                                    extra={
                                        "id": session_id,
                                        "event": message_data["event"],
                                    },
                                )
                        else:
                            logger.warning(
                                "received event for non-existent connection",
                                extra={
                                    "id": session_id,
                                    "event": message_data["event"],
                                },
                            )
                    elif action in ["create", "update", "delete"]:
                        # 处理会话状态更新
                        session_id = meta_data.get("id") if meta_data else None
                        logger.debug(
                            f"received session {action}",
                            extra={"id": session_id},
                        )

                except Exception as e:
                    logger.error(
                        "failed to process session update",
                        extra={"error": str(e), "payload": str(payload)},
                    )
        except Exception as e:
            logger.error(f"session update listener error: {e}")

    async def _publish_update(
        self, action: str, meta: Meta, message: Optional[Message] = None
    ):
        if not self.client:
            return
        """发布会话更新"""
        update = {
            "action": action,
            "meta": meta.model_dump(),
            "message": message.model_dump() if message else None,
        }

        try:
            payload = json.dumps(update, default=str)
            await self.client.publish(self.topic, payload)
        except Exception as e:
            logger.error(f"failed to publish session update: {e}")
            raise

    def _get_session_key(self, session_id: str) -> str:
        """获取会话键名"""
        return f"{self.prefix}{session_id}"

    def _get_ids_key(self) -> str:
        """获取会话ID集合键名"""
        return f"{self.prefix}ids"

    async def register(self, meta: Meta) -> Connection:
        """注册新连接"""
        # 序列化元数据
        if not self.client:
            raise ValueError("Redis client not initialized")
        data = json.dumps(meta.model_dump(), default=str)

        # 存储会话元数据
        session_key = self._get_session_key(meta.id)
        await self.client.set(session_key, data, ex=self.ttl)

        # 添加会话ID到集合
        ids_key = self._get_ids_key()
        await self.client.sadd(ids_key, meta.id)
        await self.client.expire(ids_key, self.ttl)

        # 创建连接
        conn = RedisConnection(self, meta)

        # 添加到活动连接
        async with self._lock:
            self.connections[meta.id] = conn

        # 发布创建事件
        await self._publish_update("create", meta)

        return conn

    async def get(self, id: str) -> Connection:
        """获取连接"""
        # 检查会话ID是否有效
        if not self.client:
            raise ValueError("Redis client not initialized")
        ids_key = self._get_ids_key()
        exists = await self.client.sismember(ids_key, id)
        if not exists:
            raise SessionNotFoundError(id)

        # 获取会话元数据
        session_key = self._get_session_key(id)
        data = await self.client.get(session_key)
        if not data:
            raise SessionNotFoundError(id)

        # 续期TTL
        await self.client.expire(session_key, self.ttl)
        await self.client.expire(ids_key, self.ttl)

        # 反序列化元数据
        meta_dict = json.loads(data)
        # 处理datetime字段
        if "created_at" in meta_dict:
            meta_dict["created_at"] = datetime.fromisoformat(
                meta_dict["created_at"]
            )
        meta = Meta(**meta_dict)

        return RedisConnection(self, meta)

    async def unregister(self, id: str):
        """注销连接"""
        # 从活动连接中移除
        async with self._lock:
            self.connections.pop(id, None)
        if not self.client:
            raise ValueError("Redis client not initialized")

        # 检查会话是否存在
        ids_key = self._get_ids_key()
        exists = await self.client.sismember(ids_key, id)
        if not exists:
            raise SessionNotFoundError(id)

        # 删除会话数据
        session_key = self._get_session_key(id)
        await self.client.delete(session_key)

        # 从ID集合中移除
        await self.client.srem(ids_key, id)

        # 发布删除事件
        meta = Meta(
            id=id,
            created_at=datetime.now(),
            prefix="",
            type="",
            request=RequestInfo(headers={}, queries={}, cookies={}),
        )
        await self._publish_update("delete", meta)

    async def list(self) -> list[Connection]:
        """列出所有连接"""
        # 获取所有会话ID
        if not self.client:
            raise ValueError("Redis client not initialized")
        ids_key = self._get_ids_key()
        session_ids = await self.client.smembers(ids_key)

        connections = []
        for session_id in session_ids:
            try:
                session_key = self._get_session_key(session_id.decode("utf-8"))
                data = await self.client.get(session_key)
                if data:
                    meta_dict = json.loads(data)
                    # 处理datetime字段
                    if "created_at" in meta_dict:
                        meta_dict["created_at"] = datetime.fromisoformat(
                            meta_dict["created_at"]
                        )
                    meta = Meta(**meta_dict)
                    connections.append(RedisConnection(self, meta))
            except Exception as e:
                logger.error(
                    "failed to get session metadata",
                    extra={
                        "session_id": session_id.decode("utf-8"),
                        "error": str(e),
                    },
                )
                continue

        return connections


async def create_redis_store(config: SessionRedisConfig) -> RedisStore:
    """创建Redis存储实例"""
    store = RedisStore(config)
    await store.initialize()
    return store
