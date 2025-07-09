"""
Bootstrap 模块 - 负责应用启动时的初始化工作
"""

from typing import Optional

from myunla.models.user import Role, Tenant, User
from myunla.repos import async_db_ops
from myunla.utils.logger import get_logger

logger = get_logger(__name__)


async def create_default_tenant() -> Optional[Tenant]:
    """
    创建默认租户

    Returns:
        Optional[Tenant]: 创建的租户对象，如果已存在或创建失败则返回None
    """
    try:
        # 检查是否已存在默认租户
        existing_tenant = await async_db_ops.query_tenant_by_name("default")
        if existing_tenant:
            logger.info("默认租户已存在，跳过创建")
            return existing_tenant

        # 创建默认租户
        default_tenant = Tenant(
            name="default",
            prefix="/mcp",
            description="系统默认租户",
            is_active=True,
        )

        created_tenant = await async_db_ops.create_tenant(default_tenant)
        logger.info("默认租户创建成功: default (前缀: /mcp)")
        return created_tenant

    except Exception as e:
        logger.error(f"创建默认租户失败: {e}")
        return None


async def create_default_admin() -> Optional[User]:
    """
    创建默认管理员用户

    Returns:
        Optional[User]: 创建的用户对象，如果已存在或创建失败则返回None
    """
    try:
        # 检查是否已存在 admin 用户
        existing_admin = await async_db_ops.query_user_by_username("admin")
        if existing_admin:
            logger.info("默认管理员用户已存在，跳过创建")
            return existing_admin

        # 使用 fastapi-users 的密码哈希机制
        from fastapi_users.password import PasswordHelper

        from myunla.models.user import utc_now

        # 创建密码哈希助手
        password_helper = PasswordHelper()
        hashed_password = password_helper.hash("admin1")

        current_time = utc_now()

        admin_user = User(
            username="admin",
            email="admin@myunla.local",
            hashed_password=hashed_password,
            role=Role.ADMIN.value,
            is_superuser=True,
            is_staff=True,
            is_active=True,
            is_verified=True,
            date_joined=current_time,
            gmt_created=current_time,
            gmt_updated=current_time,
        )

        created_user = await async_db_ops.create_user(admin_user)
        logger.info("默认管理员用户创建成功: admin (密码: admin)")
        return created_user

    except Exception as e:
        logger.error(f"创建默认管理员用户失败: {e}")
        return None


async def initialize_default_data() -> bool:
    """
    初始化默认数据

    Returns:
        bool: 初始化是否成功
    """
    try:
        logger.info("开始初始化默认数据...")

        # 创建默认租户
        tenant = await create_default_tenant()

        # 创建默认管理员用户
        admin = await create_default_admin()

        success = tenant is not None and admin is not None

        if success:
            logger.info("默认数据初始化完成")
        else:
            logger.warning("默认数据初始化部分失败")

        return success

    except Exception as e:
        logger.error(f"默认数据初始化失败: {e}")
        return False


async def check_and_create_default_data(enabled: bool = True) -> bool:
    """
    检查并创建默认数据（受特性开关控制）

    Args:
        enabled: 特性开关，是否启用默认数据创建

    Returns:
        bool: 操作是否成功
    """
    if not enabled:
        logger.info("默认数据创建功能已禁用")
        return True

    try:
        return await initialize_default_data()
    except Exception as e:
        logger.error(f"检查和创建默认数据失败: {e}")
        return False
