"""Notifier配置模型"""

import os
import tempfile
from typing import Optional

from pydantic import BaseModel, Field


class NotifierRedisConfig(BaseModel):
    """Redis通知器配置"""

    addr: str = Field(default="localhost:6379", description="Redis地址")
    username: str = Field(default="", description="Redis用户名")
    password: Optional[str] = Field(default=None, description="Redis密码")
    db: int = Field(default=0, description="Redis数据库编号")
    cluster_type: str = Field(
        default="single", description="集群类型: single, cluster, sentinel"
    )
    master_name: str = Field(default="", description="哨兵模式下的主节点名称")
    topic: str = Field(default="mcp_config_updates", description="发布订阅主题")


class NotifierAPIConfig(BaseModel):
    """API通知器配置"""

    port: int = Field(default=8080, description="API服务端口")
    target_url: str = Field(default="", description="目标URL")


class NotifierSignalConfig(BaseModel):
    """信号通知器配置"""

    pid_file: str = Field(
        default_factory=lambda: os.path.join(
            tempfile.gettempdir(), "mcp_gateway.pid"
        ),
        description="PID文件路径",
    )


class NotifierConfig(BaseModel):
    """通知器配置"""

    type: str = Field(
        default="redis", description="通知器类型: redis, api, signal"
    )
    role: str = Field(
        default="sender", description="角色: sender, receiver, both"
    )
    redis: NotifierRedisConfig = Field(
        default_factory=NotifierRedisConfig, description="Redis通知器配置"
    )
    api: NotifierAPIConfig = Field(
        default_factory=NotifierAPIConfig, description="API通知器配置"
    )
    signal: NotifierSignalConfig = Field(
        default_factory=NotifierSignalConfig, description="信号通知器配置"
    )


def create_notifier_config_from_env() -> NotifierConfig:
    """从环境变量创建 notifier 配置"""
    redis_config = NotifierRedisConfig(
        addr=os.getenv("NOTIFIER_REDIS_ADDR", "localhost:6379"),
        username=os.getenv("NOTIFIER_REDIS_USERNAME", ""),
        password=os.getenv("NOTIFIER_REDIS_PASSWORD"),
        db=int(os.getenv("NOTIFIER_REDIS_DB", "0")),
        cluster_type=os.getenv("NOTIFIER_REDIS_CLUSTER_TYPE", "single"),
        master_name=os.getenv("NOTIFIER_REDIS_MASTER_NAME", ""),
        topic=os.getenv("NOTIFIER_REDIS_TOPIC", "mcp_config_updates"),
    )

    api_config = NotifierAPIConfig(
        port=int(os.getenv("NOTIFIER_API_PORT", "8080")),
        target_url=os.getenv("NOTIFIER_API_TARGET_URL", ""),
    )

    signal_config = NotifierSignalConfig(
        pid_file=os.getenv(
            "NOTIFIER_SIGNAL_PID_FILE",
            os.path.join(tempfile.gettempdir(), "mcp_gateway.pid"),
        ),
    )

    return NotifierConfig(
        type=os.getenv("NOTIFIER_TYPE", "redis"),
        role=os.getenv("NOTIFIER_ROLE", "sender"),
        redis=redis_config,
        api=api_config,
        signal=signal_config,
    )


# 默认配置实例（支持环境变量覆盖）
default_notifier_config = create_notifier_config_from_env()


# 通知器类型常量
class NotifierType:
    REDIS = "redis"
    API = "api"
    SIGNAL = "signal"
    COMPOSITE = "composite"


# 通知器角色常量
class NotifierRole:
    SENDER = "sender"
    RECEIVER = "receiver"
    BOTH = "both"
