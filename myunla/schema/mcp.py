from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from api.mcp import HttpServer, McpServer, Router, Tool
from myunla.models.user import McpConfig


class McpConfigCreate(BaseModel):
    name: str
    tenant_name: str
    servers: list[McpServer]
    routers: list[Router]
    tools: list[Tool]
    http_servers: list[HttpServer]


class McpConfigUpdate(BaseModel):
    name: str
    tenant_name: str
    servers: list[McpServer]
    routers: list[Router]
    tools: list[Tool]
    http_servers: list[HttpServer]


class McpConfigModel(BaseModel):
    id: str
    name: str
    tenant_name: str
    routers: list[Router]
    servers: list[McpServer]
    tools: list[Tool]
    http_servers: list[HttpServer]
    gmt_created: datetime
    gmt_updated: datetime
    gmt_deleted: Optional[datetime] = None

    @classmethod
    def from_orm(cls, obj: McpConfig):
        return cls(
            id=obj.id,
            name=obj.name,
            tenant_name=obj.tenant_name,
            routers=[Router(**router) for router in obj.routers],
            servers=[McpServer(**server) for server in obj.servers],
            tools=[Tool(**tool) for tool in obj.tools],
            http_servers=[HttpServer(**server) for server in obj.http_servers],
            gmt_created=obj.gmt_created,
            gmt_updated=obj.gmt_updated,
            gmt_deleted=obj.gmt_deleted,
        )


class McpConfigName(BaseModel):
    """
    MCP config name.
    """

    id: str
    name: str
    tenant_name: str


class CallToolParams(BaseModel):
    """
    Call tool params.
    """

    tool_name: str
    args: dict[str, Any] = Field(
        default_factory=dict, description="The arguments to call the tool with."
    )
