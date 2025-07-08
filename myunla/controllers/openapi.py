"""OpenAPI相关控制器模块。"""

import json

import yaml
from fastapi import APIRouter, File, HTTPException, UploadFile

from myunla.models.user import McpConfig
from myunla.repos import async_db_ops
from myunla.utils import get_logger
from oas.conv import OpenAPIConverter

router = APIRouter()
logger = get_logger(__name__)


@router.post("/openapi/import")
async def import_openapi(file: UploadFile = File(...)):
    logger.info(f"开始导入OpenAPI文件: {file.filename}")
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 文件类型检查
    if not file.filename.endswith(('.json', '.yaml', '.yml')):
        logger.warning(f"文件类型不支持: {file.filename}")
        raise HTTPException(status_code=400, detail="只支持JSON和YAML文件")

    content = await file.read()
    logger.debug(f"文件大小: {len(content)} bytes")

    # 文件大小检查
    if len(content) > 5 * 1024 * 1024:  # 5MB
        logger.warning(f"文件过大: {len(content)} bytes")
        raise HTTPException(status_code=413, detail="文件过大，最大5MB")

    try:
        logger.debug("开始解析OpenAPI文件")
        converter = OpenAPIConverter(oas_content=content)
        cfg = converter.convert()

        # 转换为数据库模型
        logger.debug("转换为数据库模型")
        db_config = McpConfig(
            name=cfg.name,
            tenant_name=cfg.tenant_name,  # TODO: 从用户上下文获取tenant_name
            routers=cfg.routers,
            servers=cfg.servers,
            tools=cfg.tools,
            http_servers=cfg.http_servers,
        )

        logger.debug("保存到数据库")
        result = await async_db_ops.create_config(db_config)

        logger.info(f"OpenAPI文件导入成功: {file.filename} -> {cfg.name}")

    except ValueError as e:
        logger.error(f"文件内容无效: {file.filename} - {e}")
        raise HTTPException(status_code=400, detail=f"文件内容无效: {e}")
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        logger.error(f"文件格式错误: {file.filename} - {e}")
        raise HTTPException(status_code=400, detail=f"文件格式错误: {e}")
    except KeyError as e:
        logger.error(f"OpenAPI规范字段缺失: {file.filename} - {e}")
        raise HTTPException(
            status_code=400, detail=f"OpenAPI规范缺少必需字段: {e}"
        )
    except Exception as e:
        logger.error(f"导入失败: {file.filename} - {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {e}")

    # TODO: notify logic
    return {"status": "success", "config_id": result.id}
