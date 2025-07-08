"""通知器工厂实现"""

from myunla.config.notifier_config import (
    NotifierAPIConfig,
    NotifierConfig,
    NotifierRedisConfig,
    NotifierSignalConfig,
)
from myunla.gateway.notifier.api_notifier import APINotifier
from myunla.gateway.notifier.enums import NotifierRole, NotifierType
from myunla.gateway.notifier.notifier import Notifier, NotifierError
from myunla.gateway.notifier.redis_notifier import RedisNotifier
from myunla.gateway.notifier.signal_notifier import SignalNotifier
from myunla.utils import get_logger

logger = get_logger(__name__)


class NotifierFactory:
    """通知器工厂"""

    @staticmethod
    def create_notifier(config: NotifierConfig) -> Notifier:
        try:
            role = NotifierRole(config.role.upper())
        except ValueError:
            raise NotifierError(f"Invalid notifier role: {config.role}")

        # 解析类型并创建通知器
        try:
            notifier_type = NotifierType(config.type.upper())
        except ValueError:
            raise NotifierError(f"Invalid notifier type: {config.type}")

        if notifier_type == NotifierType.REDIS:
            return NotifierFactory._create_redis_from_config(config.redis, role)
        elif notifier_type == NotifierType.API:
            return NotifierFactory._create_api_from_config(config.api, role)
        elif notifier_type == NotifierType.SIGNAL:
            return NotifierFactory._create_signal_from_config(
                config.signal, role
            )
        else:
            raise NotifierError(f"Unsupported notifier type: {notifier_type}")

    @staticmethod
    def _create_redis_from_config(
        redis_config: NotifierRedisConfig, role: NotifierRole
    ) -> RedisNotifier:
        """从新配置对象创建Redis通知器"""
        return RedisNotifier(redis_config, role)

    @staticmethod
    def _create_api_from_config(
        api_config: NotifierAPIConfig, role: NotifierRole
    ) -> APINotifier:
        """从新配置对象创建API通知器"""
        return APINotifier(api_config, role)

    @staticmethod
    def _create_signal_from_config(
        signal_config: NotifierSignalConfig, role: NotifierRole
    ) -> SignalNotifier:
        """从新配置对象创建信号通知器"""
        return SignalNotifier(signal_config, role)
