"""pytest配置文件 - 包含公共夹具和测试配置"""

import asyncio
import os
import tempfile
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from myunla.app import app
from myunla.config.apiserver_config import app_settings
from myunla.models.base import Base
from myunla.models.user import Role, User
from myunla.utils.auth import UserManager


@pytest.fixture(scope="session")
def event_loop():
    """创建一个事件循环用于整个测试会话"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[str]:
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def test_db_url(temp_dir: str) -> str:
    """测试数据库URL"""
    return f"sqlite:///{temp_dir}/test.db"


@pytest.fixture
def async_test_db_url(temp_dir: str) -> str:
    """异步测试数据库URL"""
    return f"sqlite+aiosqlite:///{temp_dir}/test_async.db"


@pytest.fixture
async def test_engine(async_test_db_url: str):
    """测试数据库引擎"""
    engine = create_async_engine(
        async_test_db_url,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 清理
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession]:
    """测试数据库会话"""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def test_app() -> FastAPI:
    """测试应用实例"""
    return app


@pytest.fixture
def test_client(test_app: FastAPI) -> TestClient:
    """测试客户端"""
    return TestClient(test_app)


@pytest.fixture
async def async_test_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    """异步测试客户端"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_user(test_session: AsyncSession) -> User:
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_123",
        role=Role.NORMAL,
        is_active=True,
        is_verified=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def test_admin_user(test_session: AsyncSession) -> User:
    """创建测试管理员用户"""
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password="hashed_admin_password",
        role=Role.ADMIN,
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    test_session.add(admin)
    await test_session.commit()
    await test_session.refresh(admin)
    return admin


@pytest.fixture
def mock_user_manager() -> MagicMock:
    """模拟用户管理器"""
    manager = MagicMock(spec=UserManager)
    manager.password_helper = MagicMock()
    manager.password_helper.verify_and_update = AsyncMock(
        return_value=(True, None)
    )
    manager.password_helper.hash = AsyncMock(return_value="hashed_password")
    return manager


@pytest.fixture
def dsl_test_context() -> dict:
    """DSL测试上下文"""
    return {
        "user": {"name": "Alice", "age": 30, "active": True},
        "config": {"baseUrl": "https://api.example.com"},
        "args": {"userId": "123", "format": "json"},
        "numbers": [1, 2, 3, 4, 5],
        "text": "hello world",
        "users": [
            {"name": "Alice", "age": 30, "active": True},
            {"name": "Bob", "age": 25, "active": False},
            {"name": "Charlie", "age": 35, "active": True},
        ],
    }


@pytest.fixture
def sample_mcp_config() -> dict:
    """示例MCP配置"""
    return {
        "name": "test_config",
        "routers": [
            {
                "name": "test_router",
                "path": "/test",
                "methods": ["GET", "POST"],
            }
        ],
        "servers": [
            {
                "name": "test_server",
                "command": "python",
                "args": ["-m", "test_module"],
            }
        ],
        "tools": [
            {
                "name": "test_tool",
                "description": "A test tool",
                "schema": {"type": "object"},
            }
        ],
        "http_servers": [
            {
                "name": "test_http_server",
                "base_url": "http://localhost:8080",
                "headers": {"Authorization": "Bearer token"},
            }
        ],
    }


# 设置测试环境变量
@pytest.fixture(autouse=True)
def setup_test_env():
    """自动设置测试环境"""
    os.environ["TESTING"] = "1"
    # 覆盖配置以使用测试设置
    original_secret = app_settings.SECRET_KEY
    app_settings.SECRET_KEY = "test_secret_key_123456789"

    yield

    # 恢复原始配置
    app_settings.SECRET_KEY = original_secret
    os.environ.pop("TESTING", None)


# 标记装饰器
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "auth: 认证相关测试")
    config.addinivalue_line("markers", "dsl: DSL相关测试")
    config.addinivalue_line("markers", "mcp: MCP相关测试")
    config.addinivalue_line("markers", "database: 数据库相关测试")
