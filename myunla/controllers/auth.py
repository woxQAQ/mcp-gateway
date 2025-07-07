from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select

from myunla.config.apiserver_config import AsyncSessionDependency
from myunla.models.user import User
from myunla.repos import async_db_ops
from myunla.schema.auth_schema import ChangePassword, Login, UserList, UserModel
from myunla.utils import (
    COOKIE_MAX_AGE,
    UserManager,
    current_user,
    get_jwt_strategy,
    get_logger,
    get_user_manager,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    data: Login,
    session: AsyncSessionDependency,
    user_manager: UserManager = Depends(get_user_manager),
):
    logger.info(f"用户登录尝试: {data.username}")

    if not data.password:
        logger.warning(f"登录失败 - 密码为空: {data.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")

    result = await session.execute(
        select(User).where(User.username == data.username)
    )
    user = result.scalar()
    if not user:
        logger.warning(f"登录失败 - 用户不存在: {data.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")

    (
        verified,
        password_hash,
    ) = user_manager.password_helper.verify_and_update(
        data.password, user.hashed_password
    )
    if not verified:
        logger.warning(f"登录失败 - 密码错误: {data.username}")
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

    logger.info(f"用户登录成功: {data.username}")
    return UserModel.from_orm(user)


@router.post("/logout")
async def logout(response: Response):
    logger.info("用户登出")
    response.delete_cookie("session")
    return {"message": "Logged out successfully"}


@router.get("/user")
async def get_user(user: Optional[User] = Depends(current_user)):
    if not user:
        logger.warning("未授权访问用户信息")
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.debug(f"获取用户信息: {user.username}")
    return UserModel.from_orm(user)


@router.get("/users")
async def list_users(
    session: AsyncSessionDependency, user: User = Depends(current_user)
):
    logger.info(f"管理员 {user.username} 获取用户列表")
    result = await session.execute(select(User))
    users = [UserModel.from_orm(_u) for _u in result.scalars()]
    return UserList(users=users, page_result=None)


@router.post("/users/change-password")
async def change_password(
    request: Request,
    session: AsyncSessionDependency,
    data: ChangePassword,
    user_manager: UserManager = Depends(get_user_manager),
):
    logger.info(f"用户修改密码: {data.username}")
    if not data.old_password:
        logger.warning(f"修改密码失败 - 旧密码为空: {data.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not data.new_password:
        logger.warning(f"修改密码失败 - 新密码为空: {data.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not data.username:
        logger.warning(f"修改密码失败 - 用户名为空: {data.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")

    user = await async_db_ops.query_user_by_username(data.username)
    if not user:
        logger.warning(f"修改密码失败 - 用户不存在: {data.username}")
        raise HTTPException(status_code=400, detail="User not found")

    verified, _ = user_manager.password_helper.verify_and_update(
        data.old_password, user.hashed_password
    )
    if not verified:
        logger.warning(f"修改密码失败 - 旧密码错误: {data.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")

    user.hashed_password = user_manager.password_helper.hash(data.new_password)
    session.add(user)
    await session.commit()

    logger.info(f"用户密码修改成功: {data.username}")
    return UserModel.from_orm(user)


@router.delete("/users/{user_id}")
async def delete_user(
    request: Request,
    user_id: str,
    session: AsyncSessionDependency,
    user: User = Depends(current_user),
):
    logger.info(f"管理员 {user.username} 尝试删除用户: {user_id}")

    _user = await async_db_ops.query_user_by_id(user_id)
    if not _user:
        logger.warning(f"删除用户失败 - 用户不存在: {user_id}")
        raise HTTPException(status_code=400, detail="User not found")

    admin_count = await async_db_ops.query_admin_count()
    if admin_count <= 1:
        logger.warning("删除用户失败 - 不能删除最后一个管理员")
        raise HTTPException(
            status_code=400, detail="Cannot delete the last admin"
        )

    if user.id == _user.id:
        logger.warning(f"删除用户失败 - 不能删除自己: {user.username}")
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    await async_db_ops.delete_user(_user)  # 修复bug: 应该删除_user而不是user
    logger.info(f"用户删除成功: {_user.username} (删除者: {user.username})")
    return {"message": "User deleted successfully"}
