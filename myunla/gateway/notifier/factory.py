"""通知器工厂实现"""

from typing import Any, Optional

from myunla.gateway.notifier.api_notifier import APINotifier, APINotifierConfig
from myunla.gateway.notifier.enums import NotifierRole, NotifierType
from myunla.gateway.notifier.notifier import Notifier, NotifierError
from myunla.gateway.notifier.redis_notifier import (
    RedisNotifier,
    RedisNotifierConfig,
)
from myunla.gateway.notifier.signal_notifier import (
    SignalNotifier,
    SignalNotifierConfig,
)
from myunla.utils import get_logger

logger = get_logger(__name__)


class NotifierConfig:
    """通知器配置"""

    def __init__(
        self,
        role: str = "both",
        notifier_type: str = "redis",
        signal: Optional[dict[str, Any]] = None,
        api: Optional[dict[str, Any]] = None,
        redis: Optional[dict[str, Any]] = None,
    ):
        self.role = role
        self.type = notifier_type
        self.signal = signal or {}
        self.api = api or {}
        self.redis = redis or {}


class NotifierFactory:
    """通知器工厂"""

    @staticmethod
    def create_notifier(config: dict[str, Any]) -> Notifier:
        """
        根据配置创建通知器

        Args:
            config: 通知器配置字典

        Returns:
            创建的通知器实例

        Raises:
            NotifierError: 创建失败时抛出
        """
        try:
            # 解析通用配置
            role_str = config.get("role", "both").upper()
            notifier_type_str = config.get("type", "redis").upper()

            # 验证角色
            try:
                role = NotifierRole(role_str)
            except ValueError:
                raise NotifierError(f"Invalid notifier role: {role_str}")

            # 验证类型
            try:
                notifier_type = NotifierType(notifier_type_str)
            except ValueError:
                raise NotifierError(
                    f"Invalid notifier type: {notifier_type_str}"
                )

            # 根据类型创建通知器
            if notifier_type == NotifierType.REDIS:
                return NotifierFactory._create_redis_notifier(
                    config.get("redis", {}), role
                )
            elif notifier_type == NotifierType.API:
                return NotifierFactory._create_api_notifier(
                    config.get("api", {}), role
                )
            elif notifier_type == NotifierType.SIGNAL:
                return NotifierFactory._create_signal_notifier(
                    config.get("signal", {}), role
                )
            else:
                raise NotifierError(
                    f"Unsupported notifier type: {notifier_type}"
                )

        except Exception as e:
            logger.error(f"创建通知器失败: {e}")
            raise NotifierError(f"Failed to create notifier: {e}", cause=e)

    @staticmethod
    def _create_redis_notifier(
        redis_config: dict[str, Any], role: NotifierRole
    ) -> RedisNotifier:
        """创建Redis通知器"""
        config = RedisNotifierConfig(
            addr=redis_config.get("addr", "localhost:6379"),
            username=redis_config.get("username", ""),
            password=redis_config.get("password"),
            db=redis_config.get("db", 0),
            cluster_type=redis_config.get("cluster_type", "single"),
            master_name=redis_config.get("master_name", ""),
            topic=redis_config.get("topic", "mcp_config_updates"),
            role=role,
        )
        return RedisNotifier(config)

    @staticmethod
    def _create_api_notifier(
        api_config: dict[str, Any], role: NotifierRole
    ) -> APINotifier:
        """创建API通知器"""
        config = APINotifierConfig(
            port=api_config.get("port", 8080),
            role=role,
            target_url=api_config.get("target_url", ""),
        )
        return APINotifier(config)

    @staticmethod
    def _create_signal_notifier(
        signal_config: dict[str, Any], role: NotifierRole
    ) -> SignalNotifier:
        """创建信号通知器"""
        import os
        import tempfile

        # 使用系统临时目录而不是硬编码的/tmp
        default_pid_file = os.path.join(
            tempfile.gettempdir(), "mcp_gateway.pid"
        )
        pid_file = signal_config.get("pid", default_pid_file)
        config = SignalNotifierConfig(
            pid_file=pid_file,
            role=role,
        )
        return SignalNotifier(config)
