"""MCP配置数据访问层模块。"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myunla.models.user import McpConfig
from myunla.repos.base import AsyncRepository
from myunla.utils import utc_now


class AsyncMcpConfigRepository(AsyncRepository):
    """异步MCP配置数据仓库类。"""

    async def query_config_by_id(self, config_id: str):
        """根据ID查询MCP配置。"""

        async def query(session: AsyncSession):
            stmt = select(McpConfig).where(
                McpConfig.id == config_id, McpConfig.gmt_deleted.is_(None)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(query)

    async def query_config_by_name_and_tenant(
        self, name: str, tenant_name: str
    ):
        """根据名称和租户ID查询MCP配置"""

        async def query(session: AsyncSession):
            stmt = select(McpConfig).where(
                McpConfig.name == name,
                McpConfig.tenant_name == tenant_name,
                McpConfig.gmt_deleted.is_(None),
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(query)

    async def list_config_names(
        self, tenant_name: Optional[str], include_deleted: bool = False
    ) -> list[tuple[str, str, str]]:
        """获取配置名称列表"""

        async def query(session: AsyncSession):
            stmt = select(McpConfig.id, McpConfig.name, McpConfig.tenant_name)
            if not include_deleted:
                stmt = stmt.where(McpConfig.gmt_deleted.is_(None))
            if tenant_name:
                stmt = stmt.where(McpConfig.tenant_name == tenant_name)
            result = await session.execute(stmt)
            return [(row[0], row[1], row[2]) for row in result.all()]

        return await self._execute_query(query)

    async def list_configs(self, tenant_name: str | None = None):
        """获取配置列表"""

        async def query(session: AsyncSession):
            stmt = select(McpConfig).where(McpConfig.gmt_deleted.is_(None))
            if tenant_name:
                stmt = stmt.where(McpConfig.tenant_name == tenant_name)
            result = await session.execute(stmt)
            return result.scalars().all()

        return await self._execute_query(query)

    async def create_config(self, config: McpConfig):
        """创建MCP配置"""

        async def operation(session: AsyncSession):
            session.add(config)
            await session.flush()
            await session.refresh(config)
            return config

        return await self.execute_with_transaction(operation)

    async def update_config(self, config: McpConfig):
        """更新MCP配置"""

        async def operation(session: AsyncSession):
            config.gmt_updated = utc_now()
            session.add(config)
            await session.flush()
            return config

        return await self.execute_with_transaction(operation)

    async def delete_config(self, config: McpConfig):
        """软删除MCP配置"""

        async def operation(session: AsyncSession):
            config.gmt_deleted = utc_now()
            session.add(config)
            await session.flush()
            return config

        return await self.execute_with_transaction(operation)

    async def query_config_exists(self, tenant_name: str, name: str):
        """查询MCP配置是否存在"""

        async def query(session: AsyncSession):
            stmt = select(McpConfig).where(
                McpConfig.name == name,
                McpConfig.tenant_name == tenant_name,
                McpConfig.gmt_deleted.is_(None),
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

        return await self._execute_query(query)

    async def set_active(self, config_id: str):
        """设置MCP配置为激活状态 - 当前只记录操作"""

        config = await self.query_config_by_id(config_id)
        if not config:
            raise ValueError("MCP config not found")

        # 目前MCP配置激活只是记录操作，没有持久化状态
        # 如果需要持久化，可以在数据库模型中添加is_active字段
        return config
