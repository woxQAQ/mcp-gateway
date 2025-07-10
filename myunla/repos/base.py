from collections.abc import Awaitable, Callable
from typing import Optional, Protocol, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, sessionmaker

from myunla.config import (
    get_async_session,
    get_sync_session,
    sync_engine,
)

# 定义泛型类型变量
T = TypeVar('T')
R = TypeVar('R')


class AsyncRepositoryProtocol(Protocol):
    async def _execute_query(
        self, query_func: Callable[[AsyncSession], Awaitable[T]]
    ) -> T: ...

    async def execute_with_transaction(
        self, operation: Callable[[AsyncSession], Awaitable[T]]
    ) -> T: ...


class SyncRepositoryProtocol(Protocol):
    def _get_session(self) -> Session: ...

    def _execute_query(self, query_func: Callable[[Session], T]) -> T: ...

    def _execute_transaction(self, operation: Callable[[Session], T]) -> T: ...


class SyncRepository(SyncRepositoryProtocol):
    def __init__(self, session: Session):
        self._session = session

    def _get_session(self) -> Session:
        if not self._session:
            session = sessionmaker(
                sync_engine, class_=Session, expire_on_commit=False
            )
            with session() as session:
                return session
        return self._session

    def _execute_query(self, query_func: Callable[[Session], T]) -> T:
        if self._session:
            return query_func(self._session)
        session = sessionmaker(
            sync_engine, class_=Session, expire_on_commit=False
        )
        with session() as session:
            return query_func(self._session)

    def _execute_transaction(self, operation: Callable[[Session], T]) -> T:
        for session in get_sync_session():
            try:
                res = operation(session)
                session.commit()
                return res
            except Exception as e:
                session.rollback()
                raise
        # 如果 get_sync_session() 没有产生任何会话，抛出异常
        raise RuntimeError("No database session available")


class AsyncRepository(AsyncRepositoryProtocol):
    def __init__(self, session: Optional[AsyncSession]):
        self._session = session

    async def _execute_query(
        self, query_func: Callable[[AsyncSession], Awaitable[T]]
    ) -> T:
        if self._session:
            return await query_func(self._session)
        else:
            async for session in get_async_session():
                return await query_func(session)
        # 如果 get_async_session() 没有产生任何会话，抛出异常
        raise RuntimeError("No database session available")

    async def execute_with_transaction(
        self, operation: Callable[[AsyncSession], Awaitable[T]]
    ) -> T:
        if self._session:
            return await operation(self._session)
        else:
            async for session in get_async_session():
                try:
                    res = await operation(session)
                    await session.commit()
                    return res
                except Exception:
                    await session.rollback()
                    raise
        # 如果 get_async_session() 没有产生任何会话，抛出异常
        raise RuntimeError("No database session available")


# AsyncDBOps 类移到 __init__.py 中以避免循环导入
