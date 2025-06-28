import datetime
from dataclasses import dataclass

from api.enums import McpServerType, Policy


@dataclass
class Tool:
    name: str
    description: str
    method: str
    path: str
    headers: dict[str, str]
    args: list[dict[str, str]]
    request_body: str
    response_body: str
    input_schema: dict[str, str]


@dataclass
class HttpServer:
    name: str
    description: str
    url: str
    tools: list[str]


@dataclass
class McpServer:
    name: str
    type: McpServerType
    description: str
    policy: Policy
    command: str
    preinstalled: bool
    url: str


@dataclass
class Cors:
    allow_origins: list[str]
    allow_credentials: bool
    allow_methods: list[str]
    allow_headers: list[str]
    expose_headers: list[str]


@dataclass
class Router:
    prefix: str
    http_server_ref: HttpServer
    sse_prefix: str
    cors: Cors


@dataclass
class Mcp:
    name: str
    updated_at: datetime
    created_at: datetime
    deleted_at: datetime
    servers: list[McpServer]
    routers: list[Router]
    tools: list[Tool]
    http_servers: list[HttpServer]
