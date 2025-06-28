from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from myunla.config.apiserver_config import AsyncSessionDependency
from myunla.models.user import McpConfig, User
from myunla.repos import async_db_ops
from myunla.schema.mcp import (
    McpConfigCreate,
    McpConfigModel,
    McpConfigName,
    McpConfigSyncStatus,
    McpConfigUpdate,
)
from myunla.utils.auth import current_user

router = APIRouter()


@router.get("/configs/names", response_model=list[McpConfigName])
async def list_mcp_config_names(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="租户ID"),
    include_deleted: bool = Query(False, description="是否包含已删除的配置"),
    user: User = Depends(current_user),
):
    """获取MCP配置名称列表"""
    results = await async_db_ops.list_config_names(tenant_id, include_deleted)
    if user.role != "admin":
        results = [r for r in results if r.tenant_id == user.tenant_id]
    return [
        McpConfigName(id=r.id, name=r.name, tenant_id=r.tenant_id)
        for r in results
    ]


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
    data: McpConfigCreate,
    session: AsyncSessionDependency,
    user: User = Depends(current_user),
):
    """创建MCP配置"""
    # 检查是否已存在同名配置
    existing = await async_db_ops.query_config_by_name_and_tenant(
        data.name, data.tenant_id
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="MCP config with this name already exists"
        )

    config = McpConfig(
        name=data.name,
        tenant_id=data.tenant_id,
        routers=data.routers,
        servers=data.servers,
        tools=data.tools,
        http_servers=data.http_servers,
    )

    result = await async_db_ops.create_config(config)
    return McpConfigModel.from_orm(result)


@router.get("/configs", response_model=list[McpConfigModel])
async def list_mcp_configs(
    request: Request,
    tenant_id: Optional[str] = None,
    user: User = Depends(current_user),
):
    """获取MCP配置列表"""
    configs = await async_db_ops.list_configs(tenant_id)
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


@router.delete("/configs/{config_id}")
async def delete_mcp_config(
    config_id: str, request: Request, user: User = Depends(current_user)
):
    """删除MCP配置"""
    config = await async_db_ops.query_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="MCP config not found")

    await async_db_ops.delete_config(config)
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


@router.get(
    "/configs/{config_id}/sync/status", response_model=McpConfigSyncStatus
)
async def get_mcp_config_sync_status(
    config_id: str, request: Request, user: User = Depends(current_user)
):
    """获取MCP配置同步状态"""
    config = await async_db_ops.query_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="MCP config not found")

    # TODO: 实现状态查询逻辑
    return McpConfigSyncStatus(status="idle", message="No recent sync activity")
