from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select

from myunla.config.apiserver_config import AsyncSessionDependency
from myunla.models.user import Role, User
from myunla.repos import async_db_ops
from myunla.schema.auth_schema import (
    ChangePassword,
    Login,
    LoginResponse,
    MessageResponse,
    Register,
    RegisterResponse,
    UserList,
    UserModel,
    UserStatusUpdate,
    UserSummary,
)
from myunla.utils import get_logger, utc_now
from myunla.utils.i18n import get_i18n_message

from .auth_utils import (
    COOKIE_MAX_AGE,
    UserManager,
    current_admin_user,
    current_user,
    get_jwt_strategy,
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
        raise HTTPException(
            status_code=400,
            detail=get_i18n_message("auth.invalid_credentials", request),
        )

    try:
        result = await session.execute(
            select(User).where(User.username == data.username)
        )
    except Exception as e:
        logger.error(f"登录失败 - 没有这个用户: {e}")
        raise HTTPException(
            status_code=500,
            detail=get_i18n_message("auth.user_not_found", request),
        )

    user = result.scalar()
    if not user:
        logger.warning(f"登录失败 - 用户不存在: {data.username}")
        raise HTTPException(
            status_code=400,
            detail=get_i18n_message("auth.invalid_credentials", request),
        )

    (
        verified,
        password_hash,
    ) = user_manager.password_helper.verify_and_update(
        data.password, user.hashed_password
    )
    if not verified:
        logger.warning(f"登录失败 - 密码错误: {data.username}")
        raise HTTPException(
            status_code=400,
            detail=get_i18n_message("auth.invalid_credentials", request),
        )

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
    return LoginResponse(
        user=UserModel.from_orm(user),
        message=get_i18n_message("auth.login_success", request),
    )


@router.post("/register")
async def register(
    request: Request,
    data: Register,
    session: AsyncSessionDependency,
    user_manager: UserManager = Depends(get_user_manager),
):
    logger.info(f"用户注册尝试: {data.username}")

    # 验证密码确认
    if data.password != data.confirm_password:
        logger.warning(f"注册失败 - 密码确认不匹配: {data.username}")
        raise HTTPException(
            status_code=400,
            detail=get_i18n_message("auth.password_mismatch", request),
        )

    # 检查用户名是否已存在
    result = await session.execute(
        select(User).where(User.username == data.username)
    )
    if result.scalar():
        logger.warning(f"注册失败 - 用户名已存在: {data.username}")
        raise HTTPException(
            status_code=400,
            detail=get_i18n_message("auth.username_exists", request),
        )

    # 检查邮箱是否已存在（如果提供了邮箱）
    if data.email:
        result = await session.execute(
            select(User).where(User.email == data.email)
        )
        if result.scalar():
            logger.warning(f"注册失败 - 邮箱已存在: {data.email}")
            raise HTTPException(
                status_code=400,
                detail=get_i18n_message("auth.email_exists", request),
            )

    try:
        # 创建新用户

        hashed_password = user_manager.password_helper.hash(data.password)
        current_time = utc_now()

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hashed_password,
            role=Role.NORMAL.value,  # 使用枚举的字符串值
            date_joined=current_time,
            gmt_created=current_time,
            gmt_updated=current_time,
        )

        session.add(user)

        # 在提交之前先验证序列化是否成功
        user_model = UserModel.from_orm(user)

        # 只有在所有操作都成功时才提交事务
        await session.commit()
        await session.refresh(user)

        logger.info(f"用户注册成功: {data.username}")
        return RegisterResponse(
            user=user_model,
            message=get_i18n_message("auth.register_success", request),
        )

    except Exception as e:
        # 如果有任何错误，回滚事务
        await session.rollback()
        logger.error(f"注册失败，已回滚事务: {data.username}, 错误: {e!s}")
        raise HTTPException(
            status_code=500,
            detail=get_i18n_message("auth.register_failed", request),
        )


@router.post("/logout")
async def logout(request: Request, response: Response):
    logger.info("用户登出")
    response.delete_cookie("session")
    return MessageResponse(
        message=get_i18n_message("auth.logout_success", request)
    )


@router.get("/user", response_model=UserModel)
async def get_user(
    request: Request, user: Optional[User] = Depends(current_user)
):
    if not user:
        logger.warning("未授权访问用户信息")
        raise HTTPException(
            status_code=401, detail=get_i18n_message("unauthorized", request)
        )
    logger.debug(f"获取用户信息: {user.username}")
    return UserModel.from_orm(user)


@router.get("/users", response_model=UserList)
async def list_users(
    session: AsyncSessionDependency, user: User = Depends(current_admin_user)
):
    logger.info(f"管理员 {user.username} 获取用户列表")
    result = await session.execute(select(User))
    all_users = result.scalars().all()
    users = [UserSummary.from_orm(_u) for _u in all_users]
    return UserList(users=users, total=len(all_users), page_result=None)


@router.post("/users/change-password")
async def change_password(
    request: Request,
    session: AsyncSessionDependency,
    data: ChangePassword,
    current_user_obj: User = Depends(current_user),
    user_manager: UserManager = Depends(get_user_manager),
):
    logger.info(f"用户修改密码: {data.username}")
    if not data.old_password:
        logger.warning(f"修改密码失败 - 旧密码为空: {data.username}")
        raise HTTPException(
            status_code=400,
            detail=get_i18n_message("auth.invalid_credentials", request),
        )
    if not data.new_password:
        logger.warning(f"修改密码失败 - 新密码为空: {data.username}")
        raise HTTPException(
            status_code=400,
            detail=get_i18n_message("auth.invalid_credentials", request),
        )
    if not data.username:
        logger.warning(f"修改密码失败 - 用户名为空: {data.username}")
        raise HTTPException(
            status_code=400,
            detail=get_i18n_message("auth.invalid_credentials", request),
        )

    # 安全检查：用户只能修改自己的密码，除非是管理员
    if (
        current_user_obj.username != data.username
        and current_user_obj.role != Role.ADMIN.value
    ):
        logger.warning(
            f"修改密码失败 - 没有权限修改其他用户密码: {current_user_obj.username} 试图修改 {data.username}"
        )
        raise HTTPException(
            status_code=403,
            detail=get_i18n_message("auth.permission_denied", request),
        )

    user = await async_db_ops.query_user_by_username(data.username)
    if not user:
        logger.warning(f"修改密码失败 - 用户不存在: {data.username}")
        raise HTTPException(
            status_code=400,
            detail=get_i18n_message("auth.user_not_found", request),
        )

    verified, _ = user_manager.password_helper.verify_and_update(
        data.old_password, user.hashed_password
    )
    if not verified:
        logger.warning(f"修改密码失败 - 旧密码错误: {data.username}")
        raise HTTPException(
            status_code=400,
            detail=get_i18n_message("auth.invalid_credentials", request),
        )

    user.hashed_password = user_manager.password_helper.hash(data.new_password)
    session.add(user)
    await session.commit()

    logger.info(
        f"用户密码修改成功: {data.username} (操作者: {current_user_obj.username})"
    )
    return UserModel.from_orm(user)


@router.delete("/users/{user_id}")
async def delete_user(
    request: Request,
    user_id: str,
    session: AsyncSessionDependency,
    user: User = Depends(current_admin_user),
):
    logger.info(f"管理员 {user.username} 尝试删除用户: {user_id}")

    _user = await async_db_ops.query_user_by_id(user_id)
    if not _user:
        logger.warning(f"删除用户失败 - 用户不存在: {user_id}")
        raise HTTPException(
            status_code=400,
            detail=get_i18n_message("auth.user_not_found", request),
        )

    admin_count = await async_db_ops.query_admin_count()
    if admin_count <= 1:
        logger.warning("删除用户失败 - 不能删除最后一个管理员")
        raise HTTPException(
            status_code=400,
            detail=get_i18n_message("auth.last_admin_error", request),
        )

    if user.id == _user.id:
        logger.warning(f"删除用户失败 - 不能删除自己: {user.username}")
        raise HTTPException(
            status_code=400,
            detail=get_i18n_message("auth.cannot_delete_self", request),
        )

    await async_db_ops.delete_user(_user)  # 修复bug: 应该删除_user而不是user
    logger.info(f"用户删除成功: {_user.username} (删除者: {user.username})")
    return MessageResponse(
        message=get_i18n_message("auth.user_deleted", request)
    )


@router.patch("/users/{user_id}/status", response_model=UserModel)
async def update_user_status(
    request: Request,
    user_id: str,
    data: UserStatusUpdate,
    session: AsyncSessionDependency,
    user: User = Depends(current_admin_user),
):
    """修改用户状态（仅管理员）"""
    logger.info(
        f"管理员 {user.username} 修改用户状态: {user_id} -> {data.is_active}"
    )

    # 查找目标用户
    target_user = await async_db_ops.query_user_by_id(user_id)
    if not target_user:
        logger.warning(f"状态修改失败 - 用户不存在: {user_id}")
        raise HTTPException(
            status_code=404,
            detail=get_i18n_message("auth.user_not_found", request),
        )

    # 检查是否是管理员且要禁用
    if target_user.role == Role.ADMIN.value and not data.is_active:
        # 检查管理员数量
        admin_count = await async_db_ops.query_admin_count()
        if admin_count <= 1:
            logger.warning("状态修改失败 - 不能禁用最后一个管理员")
            raise HTTPException(
                status_code=400,
                detail=get_i18n_message(
                    "auth.cannot_disable_last_admin", request
                ),
            )

    # 不能修改自己的状态
    if user.id == target_user.id:
        logger.warning(f"状态修改失败 - 不能修改自己的状态: {user.username}")
        raise HTTPException(
            status_code=400,
            detail=get_i18n_message("auth.cannot_modify_self", request),
        )

    # 更新用户状态
    target_user.is_active = data.is_active
    session.add(target_user)
    await session.commit()
    await session.refresh(target_user)

    action = "启用" if data.is_active else "禁用"
    logger.info(
        f"用户状态修改成功: {target_user.username} {action} (操作者: {user.username})"
    )
    return UserModel.from_orm(target_user)
