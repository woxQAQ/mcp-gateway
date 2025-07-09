from fastapi import APIRouter, Depends, HTTPException, Query, Request

from myunla.config.apiserver_config import AsyncSessionDependency
from myunla.models.user import Tenant, User
from myunla.repos import async_db_ops
from myunla.schema.tenant_schema import (
    TenantCreate,
    TenantList,
    TenantModel,
    TenantStatusUpdate,
    TenantUpdate,
)
from myunla.utils import get_logger

from .auth_utils import current_user

router = APIRouter()
logger = get_logger(__name__)


@router.post("/tenants", response_model=TenantModel)
async def create_tenant(
    request: Request,
    data: TenantCreate,
    session: AsyncSessionDependency,
    user: User = Depends(current_user),
):
    """创建租户"""
    logger.info(f"用户 {user.username} 创建租户: {data.name}")

    try:
        # 检查租户名称是否已存在
        if await async_db_ops.check_tenant_name_exists(data.name):
            logger.warning(f"创建失败 - 租户名称已存在: {data.name}")
            raise HTTPException(status_code=400, detail="租户名称已存在")

        # 检查租户前缀是否已存在（如果提供了前缀）
        if data.prefix and await async_db_ops.check_tenant_prefix_exists(
            data.prefix
        ):
            logger.warning(f"创建失败 - 租户前缀已存在: {data.prefix}")
            raise HTTPException(status_code=400, detail="租户前缀已存在")

        # 创建租户
        tenant = Tenant(
            name=data.name,
            prefix=data.prefix,
            description=data.description,
            is_active=True,
        )

        created_tenant = await async_db_ops.create_tenant(tenant)
        logger.info(f"租户创建成功: {data.name}")
        return TenantModel.from_orm(created_tenant)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建租户失败: {data.name} - {e}")
        raise HTTPException(status_code=500, detail=f"创建失败: {e!s}")


@router.get("/tenants", response_model=TenantList)
async def list_tenants(
    request: Request,
    include_inactive: bool = Query(False, description="是否包含未激活的租户"),
    user: User = Depends(current_user),
):
    """获取租户列表"""
    logger.info(f"用户 {user.username} 获取租户列表")

    try:
        tenants = await async_db_ops.list_tenants(
            include_inactive=include_inactive
        )
        total = await async_db_ops.count_tenants(
            active_only=not include_inactive
        )

        logger.debug(f"返回 {len(tenants)} 个租户")
        return TenantList(
            tenants=[TenantModel.from_orm(tenant) for tenant in tenants],
            total=total,
        )

    except Exception as e:
        logger.error(f"获取租户列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {e!s}")


@router.get("/tenants/{tenant_id}", response_model=TenantModel)
async def get_tenant(
    request: Request,
    tenant_id: str,
    user: User = Depends(current_user),
):
    """获取单个租户信息"""
    logger.info(f"用户 {user.username} 获取租户信息: {tenant_id}")

    try:
        tenant = await async_db_ops.query_tenant_by_id(tenant_id)
        if not tenant:
            logger.warning(f"租户不存在: {tenant_id}")
            raise HTTPException(status_code=404, detail="租户不存在")

        logger.debug(f"返回租户信息: {tenant.name}")
        return TenantModel.from_orm(tenant)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取租户信息失败: {tenant_id} - {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {e!s}")


@router.put("/tenants/{tenant_id}", response_model=TenantModel)
async def update_tenant(
    request: Request,
    tenant_id: str,
    data: TenantUpdate,
    session: AsyncSessionDependency,
    user: User = Depends(current_user),
):
    """更新租户信息"""
    logger.info(f"用户 {user.username} 更新租户: {tenant_id}")

    try:
        # 查找租户
        tenant = await async_db_ops.query_tenant_by_id(tenant_id)
        if not tenant:
            logger.warning(f"更新失败 - 租户不存在: {tenant_id}")
            raise HTTPException(status_code=404, detail="租户不存在")

        # 检查租户名称是否与其他租户冲突
        if data.name and await async_db_ops.check_tenant_name_exists(
            data.name, exclude_id=tenant_id
        ):
            logger.warning(f"更新失败 - 租户名称已存在: {data.name}")
            raise HTTPException(status_code=400, detail="租户名称已存在")

        # 检查租户前缀是否与其他租户冲突
        if data.prefix and await async_db_ops.check_tenant_prefix_exists(
            data.prefix, exclude_id=tenant_id
        ):
            logger.warning(f"更新失败 - 租户前缀已存在: {data.prefix}")
            raise HTTPException(status_code=400, detail="租户前缀已存在")

        # 更新租户信息
        if data.name is not None:
            tenant.name = data.name
        if data.prefix is not None:
            tenant.prefix = data.prefix
        if data.description is not None:
            tenant.description = data.description
        if data.is_active is not None:
            tenant.is_active = data.is_active

        updated_tenant = await async_db_ops.update_tenant(tenant)
        logger.info(f"租户更新成功: {tenant.name}")
        return TenantModel.from_orm(updated_tenant)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新租户失败: {tenant_id} - {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {e!s}")


@router.patch("/tenants/{tenant_id}/status", response_model=TenantModel)
async def update_tenant_status(
    request: Request,
    tenant_id: str,
    data: TenantStatusUpdate,
    session: AsyncSessionDependency,
    user: User = Depends(current_user),
):
    """更新租户启用状态"""
    logger.info(
        f"用户 {user.username} 更新租户状态: {tenant_id} -> {data.is_active}"
    )

    try:
        # 查找租户
        tenant = await async_db_ops.query_tenant_by_id(tenant_id)
        if not tenant:
            logger.warning(f"状态更新失败 - 租户不存在: {tenant_id}")
            raise HTTPException(status_code=404, detail="租户不存在")

        # 更新状态
        tenant.is_active = data.is_active
        updated_tenant = await async_db_ops.update_tenant(tenant)

        action = "启用" if data.is_active else "禁用"
        logger.info(f"租户{action}成功: {tenant.name}")
        return TenantModel.from_orm(updated_tenant)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新租户状态失败: {tenant_id} - {e}")
        raise HTTPException(status_code=500, detail=f"状态更新失败: {e!s}")


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    request: Request,
    tenant_id: str,
    session: AsyncSessionDependency,
    user: User = Depends(current_user),
):
    """删除租户"""
    logger.info(f"用户 {user.username} 删除租户: {tenant_id}")

    try:
        # 查找租户
        tenant = await async_db_ops.query_tenant_by_id(tenant_id)
        if not tenant:
            logger.warning(f"删除失败 - 租户不存在: {tenant_id}")
            raise HTTPException(status_code=404, detail="租户不存在")

        # TODO: 检查租户是否有关联的数据（如MCP配置、用户等）
        # 暂时不做强制关联检查，由业务逻辑决定是否允许删除

        # 删除租户
        await async_db_ops.delete_tenant(tenant_id)
        logger.info(f"租户删除成功: {tenant.name}")
        return {"message": f"租户 {tenant.name} 删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除租户失败: {tenant_id} - {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {e!s}")


@router.get("/tenants/name/{tenant_name}", response_model=TenantModel)
async def get_tenant_by_name(
    request: Request,
    tenant_name: str,
    user: User = Depends(current_user),
):
    """根据名称获取租户信息"""
    logger.info(f"用户 {user.username} 根据名称获取租户: {tenant_name}")

    try:
        tenant = await async_db_ops.query_tenant_by_name(tenant_name)
        if not tenant:
            logger.warning(f"租户不存在: {tenant_name}")
            raise HTTPException(status_code=404, detail="租户不存在")

        logger.debug(f"返回租户信息: {tenant.name}")
        return TenantModel.from_orm(tenant)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取租户信息失败: {tenant_name} - {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {e!s}")
