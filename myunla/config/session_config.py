"""Redis配置模型"""

from datetime import timedelta

from pydantic import BaseModel, Field


class SessionRedisConfig(BaseModel):
    """Redis会话配置"""

    addr: str = Field(
        default="localhost:6379", description="Redis地址，支持多地址用;或,分隔"
    )
    username: str = Field(default="", description="Redis用户名")
    password: str = Field(default="", description="Redis密码")
    db: int = Field(default=0, description="Redis数据库编号")
    cluster_type: str = Field(
        default="single", description="集群类型: single, cluster, sentinel"
    )
    master_name: str = Field(default="", description="哨兵模式下的主节点名称")
    prefix: str = Field(default="session", description="会话键前缀")
    topic: str = Field(default="session_updates", description="发布订阅主题")
    ttl: timedelta = Field(default=timedelta(hours=24), description="会话TTL")


class SessionConfig(BaseModel):
    store: str = Field(
        default="memory", description="会话存储类型: memory, redis"
    )
    redis_config: SessionRedisConfig = Field(
        default=SessionRedisConfig(), description="Redis会话配置"
    )


# Redis集群类型常量
class RedisClusterType:
    SINGLE = "single"
    CLUSTER = "cluster"
    SENTINEL = "sentinel"
