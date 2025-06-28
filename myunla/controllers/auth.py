import select
from collections import UserList
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from myunla.config.apiserver_config import AsyncSessionDependency
from myunla.models.user import User
from myunla.repos import async_db_ops
from myunla.schema.auth import ChangePassword, Login, UserModel
from myunla.utils.auth import (
    COOKIE_MAX_AGE,
    UserManager,
    current_user,
    get_jwt_strategy,
    get_user_manager,
)

router = APIRouter()

router.post("/login")


async def login(
    request: Request,
    response: Response,
    data: Login,
    session: AsyncSessionDependency,
    user_manager: UserManager = Depends(get_user_manager),
):
    from sqlalchemy import select

    result = await session.execute(
        select(User).where(User.username == data.username)
    )
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    verified, password_hash = (
        await user_manager.password_helper.verify_and_update(
            data.password, user.hashed_password
        )
    )
    if not verified:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if password_hash:
        user.hashed_password = password_hash
        session.add(user)
        await session.commit()
    strategy = get_jwt_strategy()
    token = await strategy.write_token(user)
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        max_age=COOKIE_MAX_AGE,
        samesite="lax",
    )
    return UserModel.from_orm(user)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("session")
    return {"message": "Logged out successfully"}


@router.get("/user")
async def get_user(user: Optional[User] = Depends(current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return UserModel.from_orm(user)


@router.get("/users")
async def list_users(
    session: AsyncSessionDependency, user: User = Depends(current_user)
):
    result = await session.execute(select(User))
    users = [UserModel.from_orm(_u) for _u in result.scalars()]
    return UserList(users=users)


@router.post("/users/change-password")
async def change_password(
    request: Request,
    session: AsyncSessionDependency,
    data: ChangePassword,
    user_manager: UserManager = Depends(get_user_manager),
):
    user = await async_db_ops.query_user_by_username(data.username)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    verified, _ = await user_manager.password_helper.verify_and_update(
        data.old_password, user.hashed_password
    )
    if not verified:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    user.hashed_password = await user_manager.password_helper.hash(
        data.new_password
    )
    session.add(user)
    await session.commit()
    return UserModel.from_orm(user)


@router.delete("/users/{user_id}")
async def delete_user(
    request: Request,
    user_id: str,
    session: AsyncSessionDependency,
    user: User = Depends(current_user),
):
    _user = await async_db_ops.query_user_by_id(user_id)
    if not _user:
        raise HTTPException(status_code=400, detail="User not found")
    admin_count = await async_db_ops.query_admin_count()
    if admin_count <= 1:
        raise HTTPException(
            status_code=400, detail="Cannot delete the last admin"
        )
    if user.id == _user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    await async_db_ops.delete_user(user)
    return {"message": "User deleted successfully"}
