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
    """
    通知器工厂类

    使用工厂模式创建不同类型的通知器实例。支持根据配置自动选择
    合适的通知器类型（Redis、API、Signal），并设置相应的角色。

    支持的通知器类型：
    - REDIS: 基于Redis发布/订阅的通知器
    - API: 基于HTTP API的通知器
    - SIGNAL: 基于操作系统信号的通知器

    支持的角色：
    - PRODUCER: 生产者角色，负责发送通知
    - CONSUMER: 消费者角色，负责接收通知
    """

    @staticmethod
    def create_notifier(config: NotifierConfig) -> Notifier:
        """
        根据配置创建通知器实例

        这是工厂的主要方法，负责解析配置、验证参数并创建相应的通知器实例。
        创建过程包括：
        1. 验证和解析通知器角色（PRODUCER/CONSUMER）
        2. 验证和解析通知器类型（REDIS/API/SIGNAL）
        3. 根据类型调用相应的私有创建方法

        Args:
            config: 通知器配置对象，包含类型、角色和具体配置信息

        Returns:
            Notifier: 创建的通知器实例

        Raises:
            NotifierError: 当角色或类型无效，或不支持的类型时抛出

        Example:
            >>> config = NotifierConfig(
            ...     type="redis",
            ...     role="producer",
            ...     redis=RedisConfig(host="localhost", port=6379)
            ... )
            >>> notifier = NotifierFactory.create_notifier(config)
        """
        # 验证并解析通知器角色
        try:
            role = NotifierRole(config.role.upper())
        except ValueError:
            raise NotifierError(f"Invalid notifier role: {config.role}")

        # 验证并解析通知器类型
        try:
            notifier_type = NotifierType(config.type.upper())
        except ValueError:
            raise NotifierError(f"Invalid notifier type: {config.type}")

        # 根据类型创建相应的通知器实例
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
        """
        从Redis配置创建Redis通知器

        Args:
            redis_config: Redis连接和通道配置
            role: 通知器角色（生产者或消费者）

        Returns:
            RedisNotifier: 配置好的Redis通知器实例
        """
        return RedisNotifier(redis_config, role)

    @staticmethod
    def _create_api_from_config(
        api_config: NotifierAPIConfig, role: NotifierRole
    ) -> APINotifier:
        """
        从API配置创建API通知器

        Args:
            api_config: API端点和认证配置
            role: 通知器角色（生产者或消费者）

        Returns:
            APINotifier: 配置好的API通知器实例
        """
        return APINotifier(api_config, role)

    @staticmethod
    def _create_signal_from_config(
        signal_config: NotifierSignalConfig, role: NotifierRole
    ) -> SignalNotifier:
        """
        从信号配置创建信号通知器

        Args:
            signal_config: 信号类型和处理配置
            role: 通知器角色（生产者或消费者）

        Returns:
            SignalNotifier: 配置好的信号通知器实例
        """
        return SignalNotifier(signal_config, role)
