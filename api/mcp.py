from datetime import datetime
from typing import Any, Optional

import yaml
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
