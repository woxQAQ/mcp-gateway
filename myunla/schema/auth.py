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


class UserModel(BaseModel):
    id: Optional[str]
    username: Optional[str]
    email: Optional[str]
    role: Optional[str]
    is_active: Optional[bool]
    date_joined: Optional[str]

    @classmethod
    def from_orm(cls, user: User):
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            date_joined=user.date_joined.isoformat(),
        )


class PageResult(BaseModel):
    """
    PageResult info
    """

    page_number: Optional[int] = Field(None, description='The page number')
    page_size: Optional[int] = Field(None, description='The page size')
    count: Optional[int] = Field(None, description='The total count of items')


class UserList(BaseModel):
    users: Optional[list[UserModel]]
    page_result: Optional[PageResult]
