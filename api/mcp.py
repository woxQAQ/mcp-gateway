from datetime import datetime
from os import name
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
        inputSchema = []
        for arg in self.args:
            property = {
                "name": arg["name"],
                "description": arg["description"],
            }
            if arg["type"] == "array":
                items = {}
                if arg["items"]["enum"]:
                    items["enum"] = arg["items"]["enum"]
                else:
                    items["type"] = arg["items"]["type"]
                    if arg["items"]["properties"]:
                        items["properties"] = arg["items"]["properties"]
                property["items"] = items
            inputSchema[arg[name]] = property
        if self.input_schema:
            inputSchema.append(self.input_schema)

        return ToolType(
            name=self.name,
            description=self.description,
            method=self.method,
            path=self.path,
            inputSchema=inputSchema,
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


class Cors(YamlMixin, BaseModel):
    allow_origins: list[str]
    allow_credentials: bool
    allow_methods: list[str]
    allow_headers: list[str]
    expose_headers: list[str]


class Router(YamlMixin, BaseModel):
    prefix: str
    http_server_ref: HttpServer
    sse_prefix: str
    cors: Cors


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
