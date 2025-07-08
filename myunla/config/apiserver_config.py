from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends
from pydantic import Field
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

BASE_PATH = Path(__file__).parent


class ApiServerConfig(BaseSettings):
    debug: bool = Field(False, alias="DEBUG")
    database_url: str = Field(
        f"sqlite:///{BASE_PATH}/db.sqlite3", alias="DATABASE_URL"
    )
    secret_key: str = Field(
        "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        alias="SECRET_KEY",
    )
    model_config: dict[str, Any] = {}

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)


settings = ApiServerConfig()


def get_async_database_url(url: str):
    urlparts = url.split(":")
    if urlparts[0] == "sqlite":
        return f"sqlite+aiosqlite:{urlparts[1]}"
    elif urlparts[0] == "postgresql":
        return f"postgresql+asyncpg:{urlparts[1]}"
    elif urlparts[0] == "mysql":
        return f"mysql+aiomysql:{urlparts[1]}"
    else:
        raise ValueError(f"Unsupported database URL: {url}")


def get_sync_database_url(url: str):
    urlparts = url.split(":")
    if urlparts[0] == "sqlite":
        return f"sqlite:{urlparts[1]}"
    elif urlparts[0] == "postgresql":
        return f"postgresql:{urlparts[1]}"
    elif urlparts[0] == "mysql":
        return f"mysql:{urlparts[1]}"
    else:
        raise ValueError(f"Unsupported database URL: {url}")


async_engine = create_async_engine(
    get_async_database_url(settings.database_url), echo=settings.debug
)
sync_engine = create_engine(
    get_sync_database_url(settings.database_url), echo=settings.debug
)


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    async_session = async_sessionmaker(async_engine)
    async with async_session() as session:
        yield session


def get_sync_session() -> Generator[Session]:
    sync_session = sessionmaker(sync_engine)
    session = sync_session()
    try:
        yield session
    finally:
        session.close()


AsyncSessionDependency = Annotated[AsyncSession, Depends(get_async_session)]
SyncSessionDependency = Annotated[Session, Depends(get_sync_session)]
