from typing import Optional

from fastapi import HTTPException

from api.mcp import Mcp
from myunla.models.user import User
from myunla.repos import async_db_ops


async def check_mcp_tenant_permission(
    cfg: Mcp, tenant_name: Optional[str], user: User
):
    if tenant_name is None:
        raise HTTPException(status_code=400, detail="Tenant name is required")
    tenant = await async_db_ops.query_tenant_by_name(tenant_name=tenant_name)
    tenant_prefix = tenant.prefix.removesuffix("/")
    if not tenant_prefix.startwith("/"):
        tenant_prefix = "/" + tenant_prefix
    for router in cfg.routers:
        if router.prefix == tenant_prefix:
            continue
        if not router.startswith(tenant_prefix + "/"):
            raise HTTPException(status_code=403, detail="Forbidden")
    if user.role != "admin":
        user_tenants = await async_db_ops.get_user_tenants(user.id)
        if tenant_name not in user_tenants:
            raise HTTPException(status_code=403, detail="Forbidden")
    return tenant
