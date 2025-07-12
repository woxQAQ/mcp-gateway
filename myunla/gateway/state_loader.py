"""
Gateway State Loader - 负责从数据库加载MCP配置并初始化网关状态
"""

from typing import Optional

from api.mcp import Mcp
from myunla.gateway.state import State
from myunla.repos import async_db_ops
from myunla.utils import get_logger

logger = get_logger(__name__)


class GatewayStateLoader:
    """
    网关状态加载器

    负责从数据库加载MCP配置并构建网关状态
    """

    def __init__(self):
        # 使用全局的 async_db_ops 实例
        pass

    async def load_mcp_configs_from_db(
        self, tenant_name: Optional[str] = None
    ) -> list[Mcp]:
        """
        从数据库加载MCP配置

        Args:
            tenant_name: 租户名称，如果为None则加载所有租户的配置

        Returns:
            List[Mcp]: MCP配置列表
        """
        try:
            logger.info("开始从数据库加载MCP配置...")

            # 从数据库获取所有激活的MCP配置
            db_configs = await async_db_ops.list_configs(tenant_name)

            if not db_configs:
                logger.warning("数据库中没有找到MCP配置")
                return []

            # 将数据库配置转换为MCP对象
            mcp_configs = [db_config.to_mcp() for db_config in db_configs]
            logger.debug(
                f"加载MCP配置: {mcp_configs[0].name} (租户: {mcp_configs[0].tenant_name})"
            )

            logger.info(f"成功从数据库加载 {len(mcp_configs)} 个MCP配置")
            return mcp_configs

        except Exception as e:
            logger.error(f"从数据库加载MCP配置失败: {e}")
            return []

    async def initialize_gateway_state(
        self, old_state: Optional[State] = None
    ) -> State:
        """
        初始化网关状态

        Args:
            old_state: 旧的网关状态，用于传输层复用

        Returns:
            State: 新的网关状态
        """
        try:
            logger.info("开始初始化网关状态...")

            # 从数据库加载MCP配置
            mcp_configs = await self.load_mcp_configs_from_db()

            if not mcp_configs:
                logger.warning("没有可用的MCP配置，创建空状态")
                from myunla.gateway.state import Metrics

                return State(
                    mcps=[],
                    runtime={},
                    metrics=Metrics(),
                )

            # 使用State.build_from_mcp构建状态
            new_state = await State.build_from_mcp(mcp_configs, old_state)

            logger.info(
                f"网关状态初始化完成，共加载 {len(mcp_configs)} 个MCP配置"
            )
            logger.info(f"状态指标: {new_state.metrics}")

            return new_state

        except Exception as e:
            logger.error(f"网关状态初始化失败: {e}")
            # 返回一个空状态而不是失败，确保服务可用
            from myunla.gateway.state import Metrics

            return State(
                mcps=[],
                runtime={},
                metrics=Metrics(),
            )

    async def reload_gateway_state(
        self, current_state: Optional[State] = None
    ) -> State:
        """
        重新加载网关状态

        Args:
            current_state: 当前网关状态，用于传输层复用

        Returns:
            State: 新的网关状态
        """
        logger.info("开始重新加载网关状态...")
        return await self.initialize_gateway_state(current_state)


# 全局状态加载器实例
state_loader = GatewayStateLoader()
