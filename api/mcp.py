from datetime import datetime
from typing import Any, Optional

import yaml
from mcp.types import Tool as ToolType
from pydantic import BaseModel

from api.enums import McpServerType, Policy


class YamlMixin:
    """提供 YAML 字符串表示的混入类"""

    def __str__(self) -> str:
        return yaml.dump(
            self.model_dump(),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )


class Tool(YamlMixin, BaseModel):
    name: str
    description: str
    method: str
    path: str
    headers: dict[str, str]
    args: list[dict[str, Any]]
    request_body: str
    response_body: str
    input_schema: dict[str, Any]

    def to_tool_type(self) -> ToolType:
        """转换为MCP Tool类型"""
        properties = {}

        # 构建参数的properties
        for arg in self.args:
            prop = {
                "description": arg["description"],
            }

            # 添加类型信息
            if "type" in arg:
                prop["type"] = arg["type"]

            # 处理数组类型
            if arg.get("type") == "array" and "items" in arg:
                items = {}
                items_config = arg["items"]

                if items_config.get("enum"):
                    items["enum"] = items_config["enum"]
                else:
                    if "type" in items_config:
                        items["type"] = items_config["type"]
                    if items_config.get("properties"):
                        items["properties"] = items_config["properties"]

                prop["items"] = items

            properties[arg["name"]] = prop

        # 构建inputSchema
        input_schema = {
            "type": "object",
            "properties": properties,
        }

        # 添加required字段（如果存在）
        required_fields = [
            arg["name"] for arg in self.args if arg.get("required", False)
        ]
        if required_fields:
            input_schema["required"] = required_fields

        # 合并自定义的input_schema
        if self.input_schema:
            input_schema.update(self.input_schema)

        return ToolType(
            name=self.name,
            description=self.description,
            inputSchema=input_schema,
        )


class HttpServer(YamlMixin, BaseModel):
    name: str
    description: str
    url: str
    tools: list[str]


class McpServer(YamlMixin, BaseModel):
    name: str
    type: McpServerType
    description: str
    policy: Policy
    command: str
    preinstalled: bool
    url: str
    args: list[str]


class Cors(YamlMixin, BaseModel):
    allow_origins: list[str]
    allow_credentials: bool
    allow_methods: list[str]
    allow_headers: list[str]
    expose_headers: list[str]


class Router(YamlMixin, BaseModel):
    prefix: str
    server: str  # 服务器名称，可以指向HTTP服务器或MCP服务器
    sse_prefix: str
    cors: Cors

    # 为了向后兼容，保留http_server_ref但标记为可选
    http_server_ref: Optional[HttpServer] = None


class Mcp(YamlMixin, BaseModel):
    name: str
    tenant_name: str
    updated_at: Optional[datetime]
    created_at: datetime
    deleted_at: Optional[datetime]
    servers: list[McpServer]
    routers: list[Router]
    tools: list[Tool]
    http_servers: list[HttpServer]
