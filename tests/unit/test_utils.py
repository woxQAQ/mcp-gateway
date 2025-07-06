"""工具类单元测试"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from myunla.models.user import Role, User
from myunla.utils import (
    COOKIE_MAX_AGE,
    UserManager,
    get_jwt_strategy,
    get_logger,
    utc_now,
)


@pytest.mark.unit
@pytest.mark.auth
class TestUserManager:
    """用户管理器测试类"""

    def test_parse_id_string(self):
        """测试解析字符串ID"""
        manager = UserManager(MagicMock())

        # 字符串ID应该直接返回
        result = manager.parse_id("user123")
        assert result == "user123"

    def test_parse_id_non_string(self):
        """测试解析非字符串ID"""
        manager = UserManager(MagicMock())

        # 非字符串应该转换为字符串
        result = manager.parse_id(123)
        assert result == "123"

        result = manager.parse_id(None)
        assert result == "None"


@pytest.mark.unit
@pytest.mark.auth
class TestJWTStrategy:
    """JWT策略测试类"""

    def test_get_jwt_strategy(self):
        """测试获取JWT策略"""
        # Mock配置
        with patch('myunla.utils.auth.app_settings') as mock_settings:
            mock_settings.SECRET_KEY = "test_secret_key_123456789"

            strategy = get_jwt_strategy()

            assert strategy is not None
            assert strategy.lifetime_seconds == COOKIE_MAX_AGE

    def test_jwt_strategy_secret(self):
        """测试JWT策略密钥"""
        with patch('myunla.utils.auth.app_settings') as mock_settings:
            mock_settings.SECRET_KEY = "test_secret_key"

            strategy = get_jwt_strategy()
            assert strategy.secret == "test_secret_key"


@pytest.mark.unit
class TestLogger:
    """日志器测试类"""

    def test_get_logger(self):
        """测试获取日志器"""
        logger = get_logger("test_module")

        assert logger is not None
        assert logger.name == "test_module"

    def test_logger_different_modules(self):
        """测试不同模块的日志器"""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name == "module1"
        assert logger2.name == "module2"
        assert logger1 != logger2


@pytest.mark.unit
class TestUtils:
    """通用工具函数测试类"""

    def test_utc_now(self):
        """测试UTC当前时间"""
        now = utc_now()

        assert isinstance(now, datetime)
        assert now.tzinfo == UTC

        # 验证时间是最近的（在1秒内）
        current = datetime.now(UTC)
        time_diff = abs((current - now).total_seconds())
        assert time_diff < 1.0

    def test_utc_now_multiple_calls(self):
        """测试多次调用UTC时间"""
        time1 = utc_now()
        time2 = utc_now()

        # 第二次调用应该稍后
        assert time2 >= time1

        # 但差异应该很小（毫秒级）
        diff = (time2 - time1).total_seconds()
        assert diff < 0.1  # 小于100毫秒


@pytest.mark.unit
@pytest.mark.auth
class TestAuthDependencies:
    """认证依赖测试类"""

    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_current_user_authorized(self):
        """测试当前用户已授权"""
        from myunla.utils import current_user

        # 模拟请求和用户
        mock_request = MagicMock()
        mock_session = MagicMock()
        mock_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            role=Role.NORMAL,
        )

        result = await current_user(mock_request, mock_session, mock_user)

        assert result == mock_user
        assert mock_request.state.user_id == mock_user.id
        assert mock_request.state.username == mock_user.username

    @pytest.mark.auth
    @pytest.mark.asyncio
    async def test_current_user_unauthorized(self):
        """测试当前用户未授权"""
        from fastapi import HTTPException

        from myunla.utils import current_user

        mock_request = MagicMock()
        mock_session = MagicMock()

        # 用户为None表示未授权
        with pytest.raises(HTTPException) as exc_info:
            await current_user(mock_request, mock_session, None)

        assert exc_info.value.status_code == 401
        assert "Unauthorized" in str(exc_info.value.detail)


@pytest.mark.unit
class TestMcpUtils:
    """MCP工具函数测试类"""

    def test_validate_mcp_config(self):
        """测试MCP配置验证"""
        # 这里应该有MCP配置验证的具体测试
        pass

    def test_format_mcp_response(self):
        """测试MCP响应格式化"""
        # 这里应该有MCP响应格式化的具体测试
        pass

    def test_parse_mcp_request(self):
        """测试MCP请求解析"""
        # 这里应该有MCP请求解析的具体测试
        pass


@pytest.mark.unit
class TestErrorHandling:
    """错误处理测试类"""

    def test_format_validation_error(self):
        """测试验证错误格式化"""
        pass

    def test_format_database_error(self):
        """测试数据库错误格式化"""
        pass

    def test_format_authentication_error(self):
        """测试认证错误格式化"""
        pass
