from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from myunla.models.user import User


class Login(BaseModel):
    username: Optional[str] = Field(
        None, description="The username of the user"
    )
    password: Optional[str] = Field(
        None, description="The password of the user"
    )


class Register(BaseModel):
    username: str = Field(
        ..., min_length=2, max_length=50, description="The username of the user"
    )
    email: Optional[str] = Field(None, description="The email of the user")
    password: str = Field(
        ..., min_length=6, description="The password of the user"
    )
    confirm_password: str = Field(
        ..., min_length=6, description="The confirm password of the user"
    )


class ChangePassword(BaseModel):
    username: Optional[str] = Field(
        None, description="The username of the user"
    )
    old_password: Optional[str] = Field(
        None, description="The old password of the user"
    )
    new_password: Optional[str] = Field(
        None, description="The new password of the user"
    )


# 基础用户信息 Schema
class UserBase(BaseModel):
    """用户基础信息"""

    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    role: str = Field(..., description="用户角色")
    is_active: bool = Field(..., description="是否激活")
    is_verified: bool = Field(..., description="是否已验证")
    is_staff: bool = Field(..., description="是否为员工")
    is_superuser: bool = Field(..., description="是否为超级用户")
    date_joined: datetime = Field(..., description="加入时间")
    gmt_created: datetime = Field(..., description="创建时间")
    gmt_updated: datetime = Field(..., description="更新时间")

    @classmethod
    def from_orm(cls, user: User):
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            role=(
                user.role.value
                if hasattr(user.role, 'value')
                else str(user.role)
            ),
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_staff=user.is_staff,
            is_superuser=user.is_superuser,
            date_joined=user.date_joined,
            gmt_created=user.gmt_created,
            gmt_updated=user.gmt_updated,
        )

    class Config:
        from_attributes = True


# 用户详细信息 Schema（用于管理员查看）
class UserModel(UserBase):
    """完整的用户信息模型"""

    pass


# 用户简略信息 Schema（用于列表显示）
class UserSummary(BaseModel):
    """用户简略信息"""

    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    role: str = Field(..., description="用户角色")
    is_active: bool = Field(..., description="是否激活")
    date_joined: datetime = Field(..., description="加入时间")

    @classmethod
    def from_orm(cls, user: User):
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            role=(
                user.role.value
                if hasattr(user.role, 'value')
                else str(user.role)
            ),
            is_active=user.is_active,
            date_joined=user.date_joined,
        )

    class Config:
        from_attributes = True


# 登录响应 Schema
class LoginResponse(BaseModel):
    """登录响应"""

    user: UserModel = Field(..., description="用户信息")
    message: Optional[str] = Field(None, description="响应消息")


# 注册响应 Schema
class RegisterResponse(BaseModel):
    """注册响应"""

    user: UserModel = Field(..., description="用户信息")
    message: Optional[str] = Field(None, description="响应消息")


# 通用响应 Schema
class MessageResponse(BaseModel):
    """通用消息响应"""

    message: str = Field(..., description="响应消息")


class PageResult(BaseModel):
    """
    PageResult info
    """

    page_number: Optional[int] = Field(None, description='The page number')
    page_size: Optional[int] = Field(None, description='The page size')
    count: Optional[int] = Field(None, description='The total count of items')


class UserList(BaseModel):
    """用户列表响应"""

    users: list[UserSummary] = Field(..., description="用户列表")
    total: int = Field(..., description="用户总数")
    page_result: Optional[PageResult] = Field(None, description="分页信息")
