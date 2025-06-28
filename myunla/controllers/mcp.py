from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.mcp import Mcp
from myunla.config.apiserver_config import AsyncSessionDependency
from myunla.models.user import McpConfig, User
from myunla.repos import async_db_ops
from myunla.schema.mcp import (
    McpConfigModel,
    McpConfigName,
)
from myunla.utils.auth import current_user
from myunla.utils.logger import get_logger
from myunla.utils.mcp import check_mcp_tenant_permission

router = APIRouter()
logger = get_logger(__name__)


@router.get("/configs/names", response_model=list[McpConfigName])
async def list_mcp_config_names(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="租户ID"),
    include_deleted: bool = Query(False, description="是否包含已删除的配置"),
    user: User = Depends(current_user),
):
    """获取MCP配置名称列表"""
    logger.info(
        f"用户 {user.username} 获取MCP配置名称列表 (tenant_id: {tenant_id})"
    )

    results = await async_db_ops.list_config_names(
        include_deleted=include_deleted
    )
    if user.role != "admin":
        user_tenants = await async_db_ops.get_user_tenants(user.id)
        results = results.filter(lambda x: x.tenant_id in user_tenants)
    if tenant_id:
        results = results.filter(lambda x: x.tenant_id == tenant_id)

    logger.debug(f"返回 {len(results)} 个配置名称")
    return {
        'names': [result.name for result in results],
    }


@router.post("/{tenant_name}/{name}/active")
async def active_mcp_config(
    tenant_name: str,
    name: str,
    request: Request,
    user: User = Depends(current_user),
):
    """激活MCP配置"""
    logger.info(f"用户 {user.username} 激活MCP配置: {tenant_name}/{name}")

    tenant = await async_db_ops.query_tenant_by_name(tenant_name)
    if not tenant:
        logger.warning(f"激活失败 - 租户不存在: {tenant_name}")
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant_id = tenant.id
    config = await async_db_ops.query_config_by_name_and_tenant(name, tenant_id)
    if not config:
        logger.warning(f"激活失败 - 配置不存在: {tenant_name}/{name}")
        raise HTTPException(status_code=404, detail="MCP config not found")

    check_mcp_tenant_permission(config, tenant_id, user)
    await async_db_ops.set_active(config.id)

    logger.info(f"MCP配置激活成功: {tenant_name}/{name}")
    return {"message": f"MCP config {name} activated successfully"}


@router.post("/configs", response_model=McpConfigModel)
async def create_mcp_config(
    data: Mcp,
    session: AsyncSessionDependency,
    user: User = Depends(current_user),
):
    """创建MCP配置"""
    logger.info(f"用户 {user.username} 创建MCP配置: {data.name}")

    try:
        # 检查是否已存在同名配置
        existing = await async_db_ops.query_config_by_name_and_tenant(
            data.name, data.tenant_id
        )
        if existing:
            logger.warning(f"创建失败 - 配置已存在: {data.name}")
            raise HTTPException(
                status_code=400,
                detail="MCP config with this name already exists",
            )

        tenant = await async_db_ops.query_tenant_by_name(data.tenant_name)
        if not tenant:
            logger.warning(f"创建失败 - 租户不存在: {data.tenant_name}")
            raise HTTPException(status_code=400, detail="Tenant not found")

        check_mcp_tenant_permission(data, tenant.id, user)

        config = McpConfig(
            name=data.name,
            tenant_id=tenant.id,
            routers=data.routers,
            servers=data.servers,
            tools=data.tools,
            http_servers=data.http_servers,
        )

        await async_db_ops.create_config(config)
        logger.info(f"MCP配置创建成功: {data.name} (租户: {data.tenant_name})")
        return {
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建MCP配置失败: {data.name} - {e}")
        raise HTTPException(status_code=500, detail=f"创建失败: {e}")


@router.get("/configs", response_model=list[McpConfigModel])
async def list_mcp_configs(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="租户ID"),
    user: User = Depends(current_user),
):
    """获取MCP配置列表"""
    logger.info(
        f"用户 {user.username} 获取MCP配置列表 (tenant_id: {tenant_id})"
    )

    if user.role != "admin" and tenant_id:
        user_tenants = await async_db_ops.get_user_tenants(user.id)
        if tenant_id not in user_tenants:
            logger.warning(
                f"权限不足 - 用户 {user.username} 无权访问租户 {tenant_id}"
            )
            raise HTTPException(status_code=403, detail="Forbidden")

    configs = await async_db_ops.list_configs(tenant_id)
    if tenant_id:
        configs = configs.filter(lambda x: x.tenant_id == tenant_id)
    elif user.role != "admin":
        user_tenants = await async_db_ops.get_user_tenants(user.id)
        configs = configs.filter(lambda x: x.tenant_id in user_tenants)

    logger.debug(f"返回 {len(configs)} 个配置")
    return [McpConfigModel.from_orm(config) for config in configs]


@router.put("/configs", response_model=McpConfigModel)
async def update_mcp_config(
    data: Mcp,
    session: AsyncSessionDependency,
    user: User = Depends(current_user),
):
    """更新MCP配置"""
    logger.info(f"用户 {user.username} 更新MCP配置: {data.name}")

    try:
        old = async_db_ops.query_config_by_name_and_tenant(
            data.name, data.tenant_name
        )
        if not old:
            logger.warning(f"更新失败 - 配置不存在: {data.name}")
            raise HTTPException(status_code=404, detail="MCP config not found")

        if old.name != data.name:
            logger.warning(f"更新失败 - 配置名称不能修改: {data.name}")
            raise HTTPException(
                status_code=400, detail="MCP config name cannot be changed"
            )

        check_mcp_tenant_permission(data, data.tenant_name, user)
        await async_db_ops.update_config(data)

        logger.info(f"MCP配置更新成功: {data.name}")
        return {
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新MCP配置失败: {data.name} - {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {e}")


@router.delete("/configs/{tenant_id}/{name}")
async def delete_mcp_config(
    tenant_id: str,
    name: str,
    request: Request,
    user: User = Depends(current_user),
):
    """删除MCP配置"""
    logger.info(f"用户 {user.username} 删除MCP配置: {tenant_id}/{name}")

    try:
        cfg = await async_db_ops.query_config_by_name_and_tenant(
            tenant_id, name
        )
        if not cfg:
            logger.warning(f"删除失败 - 配置不存在: {tenant_id}/{name}")
            raise HTTPException(status_code=404, detail="MCP config not found")

        check_mcp_tenant_permission(cfg, tenant_id, user)
        await async_db_ops.delete_config(cfg)

        logger.info(f"MCP配置删除成功: {tenant_id}/{name}")
        return {"message": "MCP config deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除MCP配置失败: {tenant_id}/{name} - {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {e}")


@router.post("/configs/{config_id}/sync")
async def sync_mcp_config(
    config_id: str, request: Request, user: User = Depends(current_user)
):
    """同步MCP配置"""
    logger.info(f"用户 {user.username} 同步MCP配置: {config_id}")

    config = await async_db_ops.query_config_by_id(config_id)
    if not config:
        logger.warning(f"同步失败 - 配置不存在: {config_id}")
        raise HTTPException(status_code=404, detail="MCP config not found")

    # TODO: 实现同步逻辑
    logger.info(f"MCP配置同步启动: {config_id}")
    return {"message": "MCP config sync started"}
