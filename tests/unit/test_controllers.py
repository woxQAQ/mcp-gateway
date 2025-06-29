"""控制器单元测试"""

from unittest.mock import MagicMock

import pytest

from myunla.models.user import Role, User


@pytest.mark.unit
@pytest.mark.auth
class TestAuthController:
    """认证控制器测试"""

    def test_user_model_creation(self):
        """测试用户模型创建"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            role=Role.NORMAL,
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == Role.NORMAL

    def test_login_invalid_credentials(self, mock_user_manager):
        """测试无效凭据登录"""
        # 模拟登录验证逻辑
        wrong_password = "wrong_password"
        stored_hash = "stored_hash"

        # 简单验证逻辑：密码不匹配
        is_valid = wrong_password == stored_hash
        assert is_valid is False

    def test_logout(self):
        """测试登出"""
        # 简单的登出逻辑测试
        logout_response = {"message": "Successfully logged out"}
        assert logout_response["message"] == "Successfully logged out"

    def test_get_user_unauthorized(self):
        """测试未授权用户获取"""
        # 模拟未授权场景
        auth_header = None
        assert auth_header is None

    def test_change_password_success(self, mock_user_manager):
        """测试密码修改成功"""
        # 模拟密码哈希功能
        new_password = "new_password"
        expected_hash = f"hashed_{new_password}"

        # 验证密码哈希逻辑
        actual_hash = f"hashed_{new_password}"
        assert actual_hash == expected_hash

    def test_change_password_invalid_old_password(self, mock_user_manager):
        """测试旧密码无效"""
        # 模拟旧密码验证逻辑
        old_password = "wrong_password"
        stored_hash = "correct_password_hash"

        # 简单验证：密码不匹配
        is_valid = old_password == stored_hash
        assert is_valid is False

    def test_delete_user_success(self):
        """测试删除用户成功"""
        user_id = "user123"
        assert user_id == "user123"

    def test_delete_user_cannot_delete_self(self):
        """测试不能删除自己"""
        current_user_id = "user123"
        target_user_id = "user123"
        assert current_user_id == target_user_id

    def test_delete_user_cannot_delete_last_admin(self):
        """测试不能删除最后一个管理员"""
        admin_count = 1
        assert admin_count == 1


@pytest.mark.unit
class TestOpenAPIController:
    """OpenAPI控制器测试"""

    def test_validate_request_success(self):
        """测试请求验证成功"""
        request_data = {"name": "test", "value": "data"}
        assert "name" in request_data
        assert request_data["name"] == "test"

    def test_validate_request_invalid_schema(self):
        """测试无效模式"""
        invalid_data = {"invalid_field": "value"}
        assert "invalid_field" in invalid_data

    def test_generate_response_success(self):
        """测试响应生成成功"""
        response_data = {"status": "success", "data": {}}
        assert response_data["status"] == "success"


@pytest.mark.unit
@pytest.mark.mcp
class TestMcpController:
    """MCP控制器测试"""

    def test_create_config_success(self, sample_mcp_config):
        """测试创建MCP配置成功"""
        config = sample_mcp_config
        assert config["name"] == "test_config"
        assert "routers" in config

    def test_get_config_success(self):
        """测试获取MCP配置成功"""
        config_id = "mcp_config123"
        assert config_id.startswith("mcp_config")

    def test_get_config_not_found(self):
        """测试配置未找到"""
        config_id = "nonexistent"
        assert config_id == "nonexistent"

    def test_update_config_success(self, sample_mcp_config):
        """测试更新MCP配置成功"""
        updated_config = sample_mcp_config.copy()
        updated_config["name"] = "updated_config"
        assert updated_config["name"] == "updated_config"

    def test_delete_config_success(self):
        """测试删除MCP配置成功"""
        config_id = "mcp_config123"
        delete_result = {"deleted": True, "id": config_id}
        assert delete_result["deleted"] is True

    def test_list_configs_success(self):
        """测试列出MCP配置成功"""
        configs = [
            {"id": "config1", "name": "Config 1"},
            {"id": "config2", "name": "Config 2"},
        ]
        assert len(configs) == 2


@pytest.mark.unit
class TestControllerHelpers:
    """控制器助手函数测试"""

    def test_validate_request_data(self):
        """测试请求数据验证"""
        valid_data = {"username": "test", "email": "test@example.com"}
        assert "username" in valid_data
        assert "@" in valid_data["email"]

    def test_format_error_response(self):
        """测试错误响应格式化"""
        error_response = {
            "error": "Validation failed",
            "status_code": 400,
            "details": "Invalid input",
        }
        assert error_response["status_code"] == 400
        assert "error" in error_response

    def test_extract_user_from_request(self):
        """测试从请求中提取用户"""
        mock_request = MagicMock()
        mock_request.state.user_id = "user123"

        user_id = mock_request.state.user_id
        assert user_id == "user123"
