"""测试辅助函数和工具"""

from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock

from myunla.models.user import Role, User


class TestDataFactory:
    """测试数据工厂类"""

    @staticmethod
    def create_test_user(
        username: str = "testuser",
        email: str = "test@example.com",
        role: Role = Role.NORMAL,
        **kwargs,
    ) -> User:
        """创建测试用户"""
        return User(
            username=username,
            email=email,
            hashed_password="hashed_password",
            role=role,
            is_active=True,
            is_verified=True,
            **kwargs,
        )

    @staticmethod
    def create_admin_user(
        username: str = "admin", email: str = "admin@example.com", **kwargs
    ) -> User:
        """创建管理员用户"""
        return TestDataFactory.create_test_user(
            username=username,
            email=email,
            role=Role.ADMIN,
            is_superuser=True,
            **kwargs,
        )

    @staticmethod
    def create_dsl_context(
        custom_data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """创建DSL测试上下文"""
        context = {
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

        if custom_data:
            context.update(custom_data)

        return context

    @staticmethod
    def create_mcp_config(name: str = "test_config") -> dict[str, Any]:
        """创建MCP配置数据"""
        return {
            "name": name,
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


class MockFactory:
    """模拟对象工厂类"""

    @staticmethod
    def create_mock_session():
        """创建模拟数据库会话"""
        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.delete = AsyncMock()
        return session

    @staticmethod
    def create_mock_user_manager():
        """创建模拟用户管理器"""
        manager = MagicMock()
        manager.password_helper = MagicMock()
        manager.password_helper.verify_and_update = AsyncMock(
            return_value=(True, None)
        )
        manager.password_helper.hash = AsyncMock(return_value="hashed_password")
        return manager

    @staticmethod
    def create_mock_request():
        """创建模拟请求对象"""
        request = MagicMock()
        request.state = MagicMock()
        request.headers = {}
        request.query_params = {}
        return request


class DSLTestHelper:
    """DSL测试辅助类"""

    @staticmethod
    def assert_dsl_result(result, expected_value, should_succeed=True):
        """断言DSL执行结果"""
        if should_succeed:
            assert result.success, f"DSL execution failed: {result.error}"
            assert result.value == expected_value
        else:
            assert not result.success, "DSL execution should have failed"
            assert result.error is not None

class DatabaseTestHelper:
    """数据库测试辅助类"""

    @staticmethod
    async def create_and_save_user(session, **user_data) -> User:
        """创建并保存用户到数据库"""
        user = TestDataFactory.create_test_user(**user_data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def cleanup_test_data(session, *models):
        """清理测试数据"""
        for model in models:
            await session.delete(model)
        await session.commit()


class APITestHelper:
    """API测试辅助类"""

    @staticmethod
    def assert_successful_response(response, expected_status=200):
        """断言成功响应"""
        assert response.status_code == expected_status
        assert "error" not in response.json()

    @staticmethod
    def assert_error_response(
        response, expected_status=400, expected_error=None
    ):
        """断言错误响应"""
        assert response.status_code == expected_status
        if expected_error:
            response_data = response.json()
            assert "detail" in response_data or "error" in response_data

    @staticmethod
    def create_auth_headers(token: str) -> dict[str, str]:
        """创建认证头"""
        return {"Authorization": f"Bearer {token}"}


class PerformanceTestHelper:
    """性能测试辅助类"""

    @staticmethod
    def time_execution(func, *args, **kwargs):
        """测量函数执行时间"""
        import time

        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time

    @staticmethod
    async def async_time_execution(func, *args, **kwargs):
        """测量异步函数执行时间"""
        import time

        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time

    @staticmethod
    def assert_execution_time_under(execution_time: float, max_time: float):
        """断言执行时间在限制内"""
        assert (
            execution_time < max_time
        ), f"Execution took {execution_time}s, expected under {max_time}s"
