from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from myunla.models.user import Tenant, User
from myunla.repos.base import AsyncRepository

from .utils import utc_now


class AsyncUserRepository(AsyncRepository):
    async def query_user_by_id(self, user_id: str):
        """根据用户ID查询用户"""

        async def query(session: AsyncSession):
            stmt = select(User).where(
                User.id == user_id, User.gmt_deleted.is_(None)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(query)

    async def query_user_by_username(self, username: str):
        """根据用户名查询用户"""

        async def query(session: AsyncSession):
            stmt = select(User).where(
                User.username == username, User.gmt_deleted.is_(None)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(query)

    async def query_user_by_email(self, email: str):
        """根据邮箱查询用户"""

        async def query(session: AsyncSession):
            stmt = select(User).where(
                User.email == email, User.gmt_deleted.is_(None)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(query)

    async def query_user_exist(self, username: str, email: str):
        """检查用户名或邮箱是否已存在"""

        async def query(session: AsyncSession):
            stmt = select(User).where(
                or_(User.username == username, User.email == email),
                User.gmt_deleted.is_(None),
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

        return await self._execute_query(query)

    async def create_user(self, user: User):
        """创建新用户"""

        async def operation(session: AsyncSession):
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user

        return await self.execute_with_transaction(operation)

    async def delete_user(self, user: User):
        """软删除用户"""

        async def operation(session: AsyncSession):
            user.gmt_deleted = utc_now()
            user.is_active = False
            session.add(user)
            await session.flush()
            return user

        return await self.execute_with_transaction(operation)

    async def query_admin_count(self):
        """查询管理员数量"""

        async def query(session: AsyncSession):
            stmt = select(func.count(User.id)).where(
                User.is_superuser, User.gmt_deleted.is_(None)
            )
            result = await session.execute(stmt)
            return result.scalar_one()

        return await self._execute_query(query)

    # 租户相关操作
    async def query_tenant_by_name(self, tenant_name: str):
        """根据租户名称查询租户"""

        async def query(session: AsyncSession):
            stmt = select(Tenant).where(Tenant.name == tenant_name)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(query)

    async def query_tenant_by_id(self, tenant_id: str):
        """根据租户ID查询租户"""

        async def query(session: AsyncSession):
            stmt = select(Tenant).where(Tenant.id == tenant_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(query)

    async def query_tenant_by_prefix(self, prefix: str):
        """根据租户前缀查询租户"""

        async def query(session: AsyncSession):
            stmt = select(Tenant).where(Tenant.prefix == prefix)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(query)

    async def list_tenants(self, include_inactive: bool = False):
        """获取租户列表"""

        async def query(session: AsyncSession):
            stmt = select(Tenant)
            if not include_inactive:
                stmt = stmt.where(Tenant.is_active)
            stmt = stmt.order_by(Tenant.gmt_created.desc())
            result = await session.execute(stmt)
            return result.scalars().all()

        return await self._execute_query(query)

    async def create_tenant(self, tenant: Tenant):
        """创建租户"""

        async def operation(session: AsyncSession):
            session.add(tenant)
            await session.flush()
            await session.refresh(tenant)
            return tenant

        return await self.execute_with_transaction(operation)

    async def update_tenant(self, tenant: Tenant):
        """更新租户"""

        async def operation(session: AsyncSession):
            tenant.gmt_updated = utc_now()
            session.add(tenant)
            await session.flush()
            return tenant

        return await self.execute_with_transaction(operation)

    async def delete_tenant(self, tenant_id: str):
        """删除租户（硬删除）"""

        async def operation(session: AsyncSession):
            tenant = await self.query_tenant_by_id(tenant_id)
            if tenant:
                await session.delete(tenant)
                await session.flush()
            return tenant

        return await self.execute_with_transaction(operation)

    async def check_tenant_name_exists(
        self, name: str, exclude_id: str | None = None
    ):
        """检查租户名称是否已存在"""

        async def query(session: AsyncSession):
            stmt = select(Tenant).where(Tenant.name == name)
            if exclude_id:
                stmt = stmt.where(Tenant.id != exclude_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

        return await self._execute_query(query)

    async def check_tenant_prefix_exists(
        self, prefix: str, exclude_id: str | None = None
    ):
        """检查租户前缀是否已存在"""

        async def query(session: AsyncSession):
            stmt = select(Tenant).where(Tenant.prefix == prefix)
            if exclude_id:
                stmt = stmt.where(Tenant.id != exclude_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

        return await self._execute_query(query)

    async def count_tenants(self, active_only: bool = False):
        """统计租户数量"""

        async def query(session: AsyncSession):
            stmt = select(func.count(Tenant.id))
            if active_only:
                stmt = stmt.where(Tenant.is_active)
            result = await session.execute(stmt)
            return result.scalar_one()

        return await self._execute_query(query)
