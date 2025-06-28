from typing import Any

from fastapi import Depends, HTTPException, Request
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from myunla.config import AsyncSessionDependency, app_settings
from myunla.models.user import User

COOKIE_MAX_AGE = 86400


class UserManager(BaseUserManager):
    def parse_id(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        return str(value)


async def get_user_db(session: AsyncSessionDependency):
    yield SQLAlchemyUserDatabase(session, User)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=app_settings.SECRET_KEY, lifetime_seconds=COOKIE_MAX_AGE
    )


cookie_authentication = AuthenticationBackend(
    name="cookie",
    transport=CookieTransport(
        cookie_name="session", cookie_max_age=COOKIE_MAX_AGE
    ),
    get_strategy=get_jwt_strategy,
)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
):
    yield UserManager(user_db)


fastapi_users = FastAPIUsers(get_user_manager, [cookie_authentication])


async def current_user(
    request: Request,
    session: AsyncSessionDependency,
    user: User = Depends(fastapi_users.current_user(optional=True)),
):
    if user:
        request.state.user_id = user.id
        request.state.username = user.username
        return user
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
