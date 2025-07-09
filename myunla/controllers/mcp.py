from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.mcp import HttpServer, Mcp, McpServer, Router, Tool
from myunla.config import default_notifier_config
from myunla.config.apiserver_config import AsyncSessionDependency
from myunla.gateway.notifier import Notifier, NotifierError, NotifierFactory
from myunla.models.user import McpConfig, User
from myunla.repos import async_db_ops
from myunla.schema.mcp import (
    McpConfigModel,
    McpConfigName,
)
from myunla.utils import get_logger

from .auth_utils import current_user
from .mcp_utils import check_mcp_tenant_permission

router = APIRouter()
logger = get_logger(__name__)

# 全局 notifier 实例
_global_notifier: Optional[Notifier] = None


def _get_notifier() -> Notifier:
    """获取全局 notifier 实例，如果不存在则创建"""
    global _global_notifier
    if _global_notifier is None:
        # 使用配置文件中的设置，直接传递配置对象
        config = default_notifier_config

        _global_notifier = NotifierFactory.create_notifier(config)
        logger.info(
            f"创建全局 notifier 实例 (type: {config.type}, role: {config.role})"
        )
    return _global_notifier


def _convert_mcp_config_to_mcp(config: McpConfig) -> Mcp:
    """将 McpConfig 转换为 Mcp 对象"""
    return Mcp(
        name=config.name,
        tenant_name=config.tenant_name,
        created_at=config.gmt_created,
        updated_at=config.gmt_updated,
        deleted_at=config.gmt_deleted,
        routers=[Router(**router) for router in config.routers],
        servers=[McpServer(**server) for server in config.servers],
        tools=[Tool(**tool) for tool in config.tools],
        http_servers=[HttpServer(**server) for server in config.http_servers],
    )


@router.get("/configs/names", response_model=list[McpConfigName])
async def list_mcp_config_names(
    request: Request,
    tenant_name: Optional[str] = Query(None, description="租户ID"),
    include_deleted: bool = Query(False, description="是否包含已删除的配置"),
    user: User = Depends(current_user),
):
    """获取MCP配置名称列表"""
    logger.info(
        f"用户 {user.username} 获取MCP配置名称列表 (tenant_name: {tenant_name})"
    )

    results = await async_db_ops.list_config_names(
        tenant_name=tenant_name, include_deleted=include_deleted
    )
    if tenant_name:
        results = [result for result in results if result[2] == tenant_name]

    logger.debug(f"返回 {len(results)} 个配置名称")
    return {
        'names': [result[1] for result in results],
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

    config = await async_db_ops.query_config_by_name_and_tenant(
        name, tenant_name
    )
    if not config:
        logger.warning(f"激活失败 - 配置不存在: {tenant_name}/{name}")
        raise HTTPException(status_code=404, detail="MCP config not found")

    # 将McpConfig转换为Mcp对象进行权限检查
    mcp_data = _convert_mcp_config_to_mcp(config)
    await check_mcp_tenant_permission(mcp_data, tenant_name, user)

    # 激活配置 - 这里可以添加实际的激活逻辑，比如通知其他服务
    # 目前只记录激活操作

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
            data.name, data.tenant_name
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

        await check_mcp_tenant_permission(data, data.tenant_name, user)

        config = McpConfig(
            name=data.name,
            tenant_name=data.tenant_name,
            routers=[router.model_dump() for router in data.routers],
            servers=[server.model_dump() for server in data.servers],
            tools=[tool.model_dump() for tool in data.tools],
            http_servers=[server.model_dump() for server in data.http_servers],
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
    tenant_name: Optional[str] = Query(None, description="租户ID"),
    user: User = Depends(current_user),
):
    """获取MCP配置列表"""
    logger.info(
        f"用户 {user.username} 获取MCP配置列表 (tenant_name: {tenant_name})"
    )

    configs = await async_db_ops.list_configs(tenant_name)
    if tenant_name:
        configs = configs.filter(lambda x: x.tenant_name == tenant_name)

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
        old = await async_db_ops.query_config_by_name_and_tenant(
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

        await check_mcp_tenant_permission(data, data.tenant_name, user)
        await async_db_ops.update_config(McpConfig.from_mcp(data))

        logger.info(f"MCP配置更新成功: {data.name}")
        return {
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新MCP配置失败: {data.name} - {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {e}")


@router.delete("/configs/{tenant_name}/{name}")
async def delete_mcp_config(
    tenant_name: str,
    name: str,
    request: Request,
    user: User = Depends(current_user),
):
    """删除MCP配置"""
    logger.info(f"用户 {user.username} 删除MCP配置: {tenant_name}/{name}")

    try:
        # 直接使用租户名称查询配置
        logger.debug(f"查询配置: name={name}, tenant_name={tenant_name}")

        cfg = await async_db_ops.query_config_by_name_and_tenant(
            name, tenant_name
        )
        if not cfg:
            # 列出所有配置以便调试
            all_configs = await async_db_ops.list_configs()
            logger.warning(f"删除失败 - 配置不存在: {tenant_name}/{name}")
            logger.debug(
                f"现有配置: {[(c.name, c.tenant_name) for c in all_configs]}"
            )
            raise HTTPException(status_code=404, detail="MCP config not found")

        # 将McpConfig转换为Mcp对象进行权限检查
        mcp_data = _convert_mcp_config_to_mcp(cfg)
        await check_mcp_tenant_permission(mcp_data, tenant_name, user)
        await async_db_ops.delete_config(cfg)

        logger.info(f"MCP配置删除成功: {tenant_name}/{name}")
        return {"message": "MCP config deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除MCP配置失败: {tenant_name}/{name} - {e}")
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

    # 将 McpConfig 转换为 Mcp 对象进行权限检查
    mcp_data = _convert_mcp_config_to_mcp(config)
    await check_mcp_tenant_permission(mcp_data, config.tenant_name, user)

    try:
        # 获取全局 notifier 实例
        notifier = _get_notifier()

        # 发送配置更新通知
        await notifier.notify_update(mcp_data)

        logger.info(f"MCP配置同步成功: {config_id} (name: {config.name})")
        return {"message": f"MCP config {config.name} synced successfully"}

    except NotifierError as e:
        logger.error(f"同步失败 - 通知器错误: {config_id} - {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {e}")
    except Exception as e:
        logger.error(f"同步MCP配置失败: {config_id} - {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {e}")
