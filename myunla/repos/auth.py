from sqlalchemy import func, or_, select

from myunla.models.user import Tenant, User
from myunla.repos.base import AsyncRepository
from myunla.utils import utc_now


class AsyncUserRepository(AsyncRepository):
    async def query_user_by_id(self, user_id: str):
        """根据用户ID查询用户"""

        async def query(session):
            stmt = select(User).where(
                User.id == user_id, User.gmt_deleted.is_(None)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(query)

    async def query_user_by_username(self, username: str):
        """根据用户名查询用户"""

        async def query(session):
            stmt = select(User).where(
                User.username == username, User.gmt_deleted.is_(None)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(query)

    async def query_user_by_email(self, email: str):
        """根据邮箱查询用户"""

        async def query(session):
            stmt = select(User).where(
                User.email == email, User.gmt_deleted.is_(None)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(query)

    async def query_user_exist(self, username: str, email: str):
        """检查用户名或邮箱是否已存在"""

        async def query(session):
            stmt = select(User).where(
                or_(User.username == username, User.email == email),
                User.gmt_deleted.is_(None),
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

        return await self._execute_query(query)

    async def create_user(self, user: User):
        """创建新用户"""

        async def operation(session):
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user

        return await self.execute_with_transaction(operation)

    async def delete_user(self, user: User):
        """软删除用户"""

        async def operation(session):
            user.gmt_deleted = utc_now()
            user.is_active = False
            session.add(user)
            await session.flush()
            return user

        return await self.execute_with_transaction(operation)

    async def get_user_tenants(self, user_id: str):
        """获取用户所属的租户"""

        async def query(session):
            stmt = select(User.tenant_id).where(
                User.id == user_id, User.gmt_deleted.is_(None)
            )
            result = await session.execute(stmt)
            return result.all()

        return await self._execute_query(query)

    async def query_admin_count(self):
        """查询管理员数量"""

        async def query(session):
            stmt = select(func.count(User.id)).where(
                User.is_superuser, User.gmt_deleted.is_(None)
            )
            result = await session.execute(stmt)
            return result.scalar_one()

        return await self._execute_query(query)

    async def query_tenant_by_name(self, tenant_name: str):
        """根据租户名称查询租户"""

        async def query(session):
            stmt = select(Tenant).where(
                Tenant.name == tenant_name, Tenant.gmt_deleted.is_(None)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(query)
