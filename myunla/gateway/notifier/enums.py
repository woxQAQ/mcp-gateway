"""通知器相关枚举定义"""

from enum import StrEnum


class NotifierRole(StrEnum):
    """通知器角色枚举"""

    SENDER = "sender"
    RECEIVER = "receiver"
    BOTH = "both"


class NotifierType(StrEnum):
    """通知器类型枚举"""

    REDIS = "redis"
    API = "api"
    SIGNAL = "signal"
    COMPOSITE = "composite"
