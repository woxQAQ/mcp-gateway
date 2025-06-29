"""简化的pytest配置文件 - 避免循环导入问题"""

import asyncio
import os
import tempfile
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest


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


@pytest.fixture
def mock_user_manager() -> MagicMock:
    """模拟用户管理器"""
    manager = MagicMock()
    manager.password_helper = MagicMock()
    # 对于单元测试，使用同步Mock
    manager.password_helper.verify_and_update = MagicMock(
        return_value=(True, None)
    )
    manager.password_helper.hash = MagicMock(return_value="hashed_password")
    return manager


@pytest.fixture
def async_mock_user_manager() -> MagicMock:
    """异步模拟用户管理器 - 用于集成测试"""
    manager = MagicMock()
    manager.password_helper = MagicMock()
    manager.password_helper.verify_and_update = AsyncMock(
        return_value=(True, None)
    )
    manager.password_helper.hash = AsyncMock(return_value="hashed_password")
    return manager


@pytest.fixture
def test_client():
    """基础测试客户端夹具"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI(title="Test App")
    return TestClient(app)


# 设置测试环境变量
@pytest.fixture(autouse=True)
def setup_test_env():
    """自动设置测试环境"""
    os.environ["TESTING"] = "1"

    yield

    # 清理环境变量
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
