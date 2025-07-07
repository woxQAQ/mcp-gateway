"""Configuration update notifier module."""

from .api_notifier import APINotifier, APINotifierConfig
from .composite_notifier import CompositeNotifier, create_composite_notifier
from .enums import NotifierRole, NotifierType
from .factory import (
    NotifierConfig,
    NotifierFactory,
)
from .notifier import BaseNotifier, Notifier, NotifierError
from .redis_notifier import RedisNotifier, RedisNotifierConfig
from .signal_notifier import (
    SignalNotifier,
    SignalNotifierConfig,
    remove_pid_file,
    write_pid_file,
)

__all__ = [
    # 基础接口
    "Notifier",
    "BaseNotifier",
    "NotifierError",
    "NotifierRole",
    "NotifierType",
    # Redis 通知器
    "RedisNotifier",
    "RedisNotifierConfig",
    # API 通知器
    "APINotifier",
    "APINotifierConfig",
    # 信号通知器
    "SignalNotifier",
    "SignalNotifierConfig",
    "write_pid_file",
    "remove_pid_file",
    # 组合通知器
    "CompositeNotifier",
    "create_composite_notifier",
    # 工厂
    "NotifierFactory",
    "NotifierConfig",
]
