import json

import yaml
from fastapi import APIRouter, File, HTTPException, UploadFile

from myunla.models.user import McpConfig
from myunla.repos import async_db_ops
from oas.conv import OpenAPIConverter

router = APIRouter()


@router.post("/openapi/import")
async def import_openapi(file: UploadFile = File(...)):
    # 文件类型检查
    if not file.filename.endswith(('.json', '.yaml', '.yml')):
        raise HTTPException(status_code=400, detail="只支持JSON和YAML文件")

    content = await file.read()

    # 文件大小检查
    if len(content) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(status_code=413, detail="文件过大，最大5MB")

    try:
        converter = OpenAPIConverter(oas_content=content)
        cfg = converter.convert()

        # 转换为数据库模型
        db_config = McpConfig(
            name=cfg.name,
            tenant_id=cfg.tenant_name,  # TODO: 从用户上下文获取tenant_id
            routers=cfg.routers,
            servers=cfg.servers,
            tools=cfg.tools,
            http_servers=cfg.http_servers,
        )
        result = await async_db_ops.create_config(db_config)  # 添加await

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"文件内容无效: {e}")
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise HTTPException(status_code=400, detail=f"文件格式错误: {e}")
    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"文件编码错误，请使用UTF-8 {e}"
        )
    except KeyError as e:
        raise HTTPException(
            status_code=400, detail=f"OpenAPI规范缺少必需字段: {e}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {e}")

    # TODO: notify logic
    return {"status": "success", "config_id": result.id}
