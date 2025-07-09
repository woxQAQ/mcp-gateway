from typing import Optional

from fastapi import HTTPException

from api.mcp import Mcp
from myunla.models.user import User
from myunla.repos import async_db_ops
from myunla.utils import get_logger

logger = get_logger(__name__)


async def check_mcp_tenant_permission(
    cfg: Mcp, tenant_name: Optional[str], user: User
):
    if tenant_name is None:
        raise HTTPException(status_code=400, detail="Tenant name is required")

    logger.debug(f"权限检查: tenant_name={tenant_name}, user={user.username}")

    tenant = await async_db_ops.query_tenant_by_name(tenant_name=tenant_name)
    if not tenant:
        logger.warning(f"权限检查失败 - 租户不存在: {tenant_name}")
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant_prefix = tenant.prefix.removesuffix("/")
    if not tenant_prefix.startswith("/"):
        tenant_prefix = "/" + tenant_prefix

    logger.debug(f"租户前缀: {tenant_prefix}")
    logger.debug(f"配置路由数量: {len(cfg.routers)}")

    for i, router in enumerate(cfg.routers):
        logger.debug(f"检查路由 {i}: prefix={router.prefix}")
        if router.prefix == tenant_prefix:
            logger.debug(f"路由 {i} 匹配租户前缀")
            continue
        if not router.prefix.startswith(tenant_prefix + "/"):
            logger.warning(
                f"权限检查失败 - 路由前缀不匹配: router.prefix={router.prefix}, tenant_prefix={tenant_prefix}"
            )
            raise HTTPException(status_code=403, detail="Forbidden")
        logger.debug(f"路由 {i} 以租户前缀开头")

    logger.debug("权限检查通过")
    return tenant
