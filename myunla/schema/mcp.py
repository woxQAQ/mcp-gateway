from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from api.mcp import Mcp


class McpConfigCreate(Mcp):
    pass


class McpConfigUpdate(BaseModel):
    mcp: Mcp


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
    """
    MCP config name.
    """

    id: str
    name: str
    tenant_id: str


class CallToolParams(BaseModel):
    """
    Call tool params.
    """

    tool_name: str
    args: dict[str, Any] = Field(
        default_factory=dict, description="The arguments to call the tool with."
    )
