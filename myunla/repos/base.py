from typing import Optional, Protocol

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, sessionmaker

from myunla.config import get_async_session, get_sync_session, sync_engine


class AsyncRepositoryProtocol(Protocol):
    async def _execute_query(self, query_func): ...

    async def execute_with_transaction(self, operation): ...


class SyncRepositoryProtocol(Protocol):
    def _get_session(self) -> Session: ...

    def _execute_query(self, query_func): ...

    def _execute_transaction(self, operation): ...


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

    def _execute_query(self, query_func):
        if self._session:
            return query_func(self._session)
        session = sessionmaker(
            sync_engine, class_=Session, expire_on_commit=False
        )
        with session() as session:
            return query_func(self._session)

    def _execute_transaction(self, operation):
        for session in get_sync_session():
            try:
                res = operation(session)
                session.commit()
                return res
            except Exception as e:
                session.rollback()
                raise


class AsyncRepository(AsyncRepositoryProtocol):
    def __init__(self, session: Optional[AsyncSession]):
        self._session = session

    async def _execute_query(self, query_func):
        if self._session:
            return await query_func(self._session)
        else:
            async_session = get_async_session()
            async with async_session() as session:
                return await query_func(session)

    async def execute_with_transaction(self, operation):
        if self._session:
            return await operation(self._session)
        else:
            for session in get_async_session():
                try:
                    res = await operation(session)
                    await session.commit()
                    return res
                except Exception:
                    await session.rollback()
                    raise


# AsyncDBOps 类移到 __init__.py 中以避免循环导入
