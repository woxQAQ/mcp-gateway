from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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

    def __str__(self) -> str:
        args_str = ""
        if self.args:
            args_list = []
            for arg in self.args:
                arg_parts = [f"name={arg.get('name', '')}"]
                if arg.get('type'):
                    arg_parts.append(f"type={arg['type']}")
                if arg.get('required'):
                    arg_parts.append("required=True")
                if arg.get('position'):
                    arg_parts.append(f"position={arg['position']}")
                args_list.append(f"      - {', '.join(arg_parts)}")
            args_str = "\n    Args:\n" + "\n".join(args_list)

        return f"""  Tool: {self.name}
    Description: {self.description}
    Method: {self.method.upper()}
    Path: {self.path}{args_str}"""


@dataclass
class HttpServer:
    name: str
    description: str
    url: str
    tools: list[str]

    def __str__(self) -> str:
        tools_str = ""
        if self.tools:
            tools_str = f"\n    Tools: {', '.join(self.tools)}"
        
        return f"""  HTTP Server: {self.name}
    Description: {self.description}
    URL: {self.url}{tools_str}"""


@dataclass
class McpServer:
    name: str
    type: McpServerType
    description: str
    policy: Policy
    command: str
    preinstalled: bool
    url: str

    def __str__(self) -> str:
        return f"""  MCP Server: {self.name}
    Type: {self.type}
    Description: {self.description}
    Policy: {self.policy}
    Command: {self.command}
    Preinstalled: {'Yes' if self.preinstalled else 'No'}
    URL: {self.url}"""


@dataclass
class Cors:
    allow_origins: list[str]
    allow_credentials: bool
    allow_methods: list[str]
    allow_headers: list[str]
    expose_headers: list[str]

    def __str__(self) -> str:
        return f"""    CORS Configuration:
      Allow Origins: {', '.join(self.allow_origins)}
      Allow Credentials: {'Yes' if self.allow_credentials else 'No'}
      Allow Methods: {', '.join(self.allow_methods)}
      Allow Headers: {', '.join(self.allow_headers)}
      Expose Headers: {', '.join(self.expose_headers)}"""


@dataclass
class Router:
    prefix: str
    http_server_ref: HttpServer
    sse_prefix: str
    cors: Cors

    def __str__(self) -> str:
        return f"""  Router:
    Prefix: {self.prefix}
    SSE Prefix: {self.sse_prefix}
    HTTP Server: {self.http_server_ref.name}
{self.cors}"""


@dataclass
class Mcp:
    name: str
    tenant_name: str
    updated_at: Optional[datetime]
    created_at: datetime
    deleted_at: datetime
    servers: Optional[list[McpServer]]
    routers: Optional[list[Router]]
    tools: Optional[list[Tool]]
    http_servers: Optional[list[HttpServer]]

    def __str__(self) -> str:
        result = [f"MCP Configuration: {self.name}"]
        result.append(f"Tenant: {self.tenant_name}")
        result.append(
            f"Created At: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        if self.updated_at:
            result.append(
                f"Updated At: {self.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        if self.http_servers:
            result.append(f"\nHTTP Servers ({len(self.http_servers)}):")
            for server in self.http_servers:
                result.append(str(server))

        if self.servers:
            result.append(f"\nMCP Servers ({len(self.servers)}):")
            for server in self.servers:
                result.append(str(server))

        if self.routers:
            result.append(f"\nRouters ({len(self.routers)}):")
            for router in self.routers:
                result.append(str(router))

        if self.tools:
            result.append(f"\nTools ({len(self.tools)}):")
            for tool in self.tools:
                result.append(str(tool))

        return "\n".join(result)
