from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from myunla.models.user import Tenant


class TenantCreate(BaseModel):
    """创建租户的数据结构"""

    name: str = Field(..., min_length=1, max_length=256, description="租户名称")
    prefix: Optional[str] = Field(None, max_length=256, description="租户前缀")
    description: Optional[str] = Field(
        None, max_length=256, description="租户描述"
    )


class TenantUpdate(BaseModel):
    """更新租户的数据结构"""

    name: Optional[str] = Field(
        None, min_length=1, max_length=256, description="租户名称"
    )
    prefix: Optional[str] = Field(None, max_length=256, description="租户前缀")
    description: Optional[str] = Field(
        None, max_length=256, description="租户描述"
    )
    is_active: Optional[bool] = Field(None, description="是否激活")


class TenantModel(BaseModel):
    """租户数据模型"""

    id: str
    name: str
    prefix: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    gmt_created: datetime
    gmt_updated: datetime

    @classmethod
    def from_orm(cls, tenant: Tenant):
        return cls(
            id=tenant.id,
            name=tenant.name,
            prefix=tenant.prefix,
            description=tenant.description,
            is_active=tenant.is_active,
            gmt_created=tenant.gmt_created,
            gmt_updated=tenant.gmt_updated,
        )


class TenantList(BaseModel):
    """租户列表数据结构"""

    tenants: list[TenantModel]
    total: int = Field(description="总数量")


class TenantStatusUpdate(BaseModel):
    """租户状态更新数据结构"""

    is_active: bool = Field(description="是否激活")
