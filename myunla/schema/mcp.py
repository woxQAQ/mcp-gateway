from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from api.mcp import Mcp


class McpConfigCreate(Mcp):
    pass


class McpConfigUpdate(BaseModel):
    name: Optional[str] = None
    routers: Optional[list[dict[str, Any]]] = None
    servers: Optional[list[dict[str, Any]]] = None
    tools: Optional[list[dict[str, Any]]] = None
    http_servers: Optional[list[dict[str, Any]]] = None


class McpConfigModel(Mcp):
    id: str
    gmt_created: datetime
    gmt_updated: datetime
    gmt_deleted: Optional[datetime] = None

    @classmethod
    def from_orm(cls, obj: Mcp):
        return cls(
            id=obj.id,
            name=obj.name,
            routers=obj.routers,
        )


class McpConfigName(BaseModel):
    id: str
    name: str
    tenant_id: str


class McpConfigSyncStatus(BaseModel):
    status: str
    last_sync: Optional[datetime] = None
    message: Optional[str] = None
