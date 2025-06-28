from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.mcp import Mcp
from myunla.config.apiserver_config import AsyncSessionDependency
from myunla.models.user import McpConfig, User
from myunla.repos import async_db_ops
from myunla.schema.mcp import (
    McpConfigModel,
    McpConfigName,
    McpConfigUpdate,
)
from myunla.utils.auth import current_user
from myunla.utils.mcp import check_mcp_tenant_permission

router = APIRouter()


@router.get("/configs/names", response_model=list[McpConfigName])
async def list_mcp_config_names(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="租户ID"),
    include_deleted: bool = Query(False, description="是否包含已删除的配置"),
    user: User = Depends(current_user),
):
    """获取MCP配置名称列表"""
    results = await async_db_ops.list_config_names(
        include_deleted=include_deleted
    )
    if user.role != "admin":
        user_tenants = await async_db_ops.get_user_tenants(user.id)
        results = results.filter(lambda x: x.tenant_id in user_tenants)
    if tenant_id:
        results = results.filter(lambda x: x.tenant_id == tenant_id)
    return {
        'names': [result.name for result in results],
    }


@router.post("/{tenant_id}/{name}/active")
async def active_mcp_config(
    tenant_id: str,
    name: str,
    request: Request,
    user: User = Depends(current_user),
):
    """激活MCP配置"""
    config = await async_db_ops.query_config_by_name_and_tenant(name, tenant_id)
    if not config:
        raise HTTPException(status_code=404, detail="MCP config not found")

    # TODO: 实现激活逻辑
    return {"message": f"MCP config {name} activated successfully"}


@router.post("/configs", response_model=McpConfigModel)
async def create_mcp_config(
    data: Mcp,
    session: AsyncSessionDependency,
    user: User = Depends(current_user),
):
    """创建MCP配置"""
    if data.name is None:
        raise HTTPException(
            status_code=400, detail="MCP config name is required"
        )
    # 检查是否已存在同名配置
    existing = await async_db_ops.query_config_by_name_and_tenant(
        data.name, data.tenant_id
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="MCP config with this name already exists"
        )
    check_mcp_tenant_permission(data, data.tenant_id, user)

    config = McpConfig(
        name=data.name,
        tenant_id=data.tenant_id,
        routers=data.routers,
        servers=data.servers,
        tools=data.tools,
        http_servers=data.http_servers,
    )

    await async_db_ops.create_config(config)
    return {
        "status": "success",
    }


@router.get("/configs", response_model=list[McpConfigModel])
async def list_mcp_configs(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="租户ID"),
    user: User = Depends(current_user),
):
    """获取MCP配置列表"""
    if user.role != "admin" and tenant_id:
        user_tenants = await async_db_ops.get_user_tenants(user.id)
        if tenant_id not in user_tenants:
            raise HTTPException(status_code=403, detail="Forbidden")
    configs = await async_db_ops.list_configs(tenant_id)
    if tenant_id:
        configs = configs.filter(lambda x: x.tenant_id == tenant_id)
    elif user.role != "admin":
        user_tenants = await async_db_ops.get_user_tenants(user.id)
        configs = configs.filter(lambda x: x.tenant_id in user_tenants)
    return [McpConfigModel.from_orm(config) for config in configs]


@router.put("/configs/{config_id}", response_model=McpConfigModel)
async def update_mcp_config(
    config_id: str,
    data: McpConfigUpdate,
    session: AsyncSessionDependency,
    user: User = Depends(current_user),
):
    """更新MCP配置"""
    config = await async_db_ops.query_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="MCP config not found")

    # 更新字段
    if data.name is not None:
        config.name = data.name
    if data.routers is not None:
        config.routers = data.routers
    if data.servers is not None:
        config.servers = data.servers
    if data.tools is not None:
        config.tools = data.tools
    if data.http_servers is not None:
        config.http_servers = data.http_servers

    result = await async_db_ops.update_config(config)
    return McpConfigModel.from_orm(result)


@router.delete("/configs/{tenant_id}/{name}")
async def delete_mcp_config(
    tenant_id: str,
    name: str,
    request: Request,
    user: User = Depends(current_user),
):
    """删除MCP配置"""
    cfg = await async_db_ops.query_config_by_name_and_tenant(tenant_id, name)
    if not cfg:
        raise HTTPException(status_code=404, detail="MCP config not found")
    check_mcp_tenant_permission(cfg, tenant_id, user)
    await async_db_ops.delete_config(cfg)
    return {"message": "MCP config deleted successfully"}


@router.post("/configs/{config_id}/sync")
async def sync_mcp_config(
    config_id: str, request: Request, user: User = Depends(current_user)
):
    """同步MCP配置"""
    config = await async_db_ops.query_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="MCP config not found")

    # TODO: 实现同步逻辑
    return {"message": "MCP config sync started"}
