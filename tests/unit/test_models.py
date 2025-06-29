"""模型单元测试"""

import pytest

from myunla.models.user import (
    AuditLog,
    AuditResource,
    McpConfig,
    Role,
    Tenant,
    User,
    UserTenant,
)


@pytest.mark.unit
@pytest.mark.database
class TestUserModel:
    """用户模型测试类"""

    def test_user_creation(self):
        """测试用户创建"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            role=Role.NORMAL,
            is_active=True,
            is_verified=True,
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == Role.NORMAL
        assert user.is_active is True
        assert user.is_verified is True

    def test_user_id_generation(self):
        """测试用户ID生成"""
        # 测试ID生成函数
        from myunla.models.base import random_id

        user_id = "user" + random_id()
        assert user_id.startswith("user")
        assert len(user_id) > 4  # 应该有随机后缀

    def test_password_property(self):
        """测试密码属性"""
        user = User(username="test", hashed_password="original")

        # 读取密码应该抛出异常
        with pytest.raises(AttributeError):
            _ = user.password

        # 设置密码应该更新hashed_password
        user.password = "new_password"
        assert user.hashed_password == "new_password"

    def test_role_enum(self):
        """测试角色枚举"""
        assert Role.NORMAL == "normal"
        assert Role.ADMIN == "admin"

        # 测试可以设置不同角色
        user1 = User(username="user1", hashed_password="pwd", role=Role.NORMAL)
        user2 = User(username="user2", hashed_password="pwd", role=Role.ADMIN)

        assert user1.role == Role.NORMAL
        assert user2.role == Role.ADMIN

    def test_timestamps(self):
        """测试时间戳字段"""
        from myunla.utils.utils import utc_now

        now = utc_now()
        user = User(
            username="test",
            hashed_password="pwd",
            gmt_created=now,
            gmt_updated=now,
            date_joined=now,
        )

        # 验证时间戳设置
        assert user.gmt_created == now
        assert user.gmt_updated == now
        assert user.date_joined == now


@pytest.mark.unit
@pytest.mark.database
class TestTenantModel:
    """租户模型测试类"""

    def test_tenant_creation(self):
        """测试租户创建"""
        tenant = Tenant(
            name="test_tenant",
            prefix="test",
            description="Test tenant",
            is_active=True,
        )

        assert tenant.name == "test_tenant"
        assert tenant.prefix == "test"
        assert tenant.description == "Test tenant"
        assert tenant.is_active is True

    def test_tenant_id_generation(self):
        """测试租户ID生成"""
        from myunla.models.base import random_id

        tenant_id = "tenant" + random_id()
        assert tenant_id.startswith("tenant")


@pytest.mark.unit
@pytest.mark.database
class TestUserTenantModel:
    """用户租户关联模型测试类"""

    def test_user_tenant_creation(self):
        """测试用户租户关联创建"""
        user_tenant = UserTenant(
            user_id="user123",
            tenant_id="tenant456",
        )

        assert user_tenant.user_id == "user123"
        assert user_tenant.tenant_id == "tenant456"


@pytest.mark.unit
@pytest.mark.database
@pytest.mark.mcp
class TestMcpConfigModel:
    """MCP配置模型测试类"""

    def test_mcp_config_creation(self, sample_mcp_config):
        """测试MCP配置创建"""
        config = McpConfig(
            name=sample_mcp_config["name"],
            tenant_id="tenant123",
            routers=sample_mcp_config["routers"],
            servers=sample_mcp_config["servers"],
            tools=sample_mcp_config["tools"],
            http_servers=sample_mcp_config["http_servers"],
        )

        assert config.name == "test_config"
        assert config.tenant_id == "tenant123"
        assert len(config.routers) == 1
        assert len(config.servers) == 1
        assert len(config.tools) == 1
        assert len(config.http_servers) == 1

    def test_mcp_config_id_generation(self):
        """测试MCP配置ID生成"""
        from myunla.models.base import random_id

        config_id = "mcp_config" + random_id()
        assert config_id.startswith("mcp_config")

    def test_mcp_config_json_fields(self):
        """测试MCP配置JSON字段"""
        routers = [{"name": "router1", "path": "/api"}]
        servers = [{"name": "server1", "command": "python"}]

        config = McpConfig(
            name="test",
            tenant_id="tenant123",
            routers=routers,
            servers=servers,
            tools=[],
            http_servers=[],
        )

        assert config.routers == routers
        assert config.servers == servers
        assert isinstance(config.routers, list)
        assert isinstance(config.servers, list)


@pytest.mark.unit
@pytest.mark.database
class TestAuditLogModel:
    """审计日志模型测试类"""

    def test_audit_log_creation(self):
        """测试审计日志创建"""
        log = AuditLog(
            user_id="user123",
            username="testuser",
            resource_type=AuditResource.USER,
            resource_id="resource456",
            api_name="create_user",
            http_method="POST",
            path="/api/users",
            status_code=201,
            request_id="req123",
            start_time=1234567890000,
        )

        assert log.user_id == "user123"
        assert log.username == "testuser"
        assert log.resource_type == AuditResource.USER
        assert log.api_name == "create_user"
        assert log.http_method == "POST"
        assert log.status_code == 201

    def test_audit_resource_enum(self):
        """测试审计资源枚举"""
        # 测试一些关键的资源类型
        assert AuditResource.USER == "user"
        assert AuditResource.AUTH == "auth"
        assert AuditResource.CONFIG == "config"
        assert AuditResource.SYSTEM == "system"

        # 验证可以设置到模型中
        log = AuditLog(
            api_name="test",
            http_method="GET",
            path="/test",
            request_id="req123",
            start_time=1234567890000,
            resource_type=AuditResource.CHAT_COMPLETION,
        )
        assert log.resource_type == AuditResource.CHAT_COMPLETION

    def test_audit_log_id_generation(self):
        """测试审计日志ID生成"""
        from myunla.models.base import random_id

        log_id = random_id()
        assert log_id is not None
        assert len(log_id) > 0

    def test_audit_log_optional_fields(self):
        """测试审计日志可选字段"""
        log = AuditLog(
            api_name="test",
            http_method="GET",
            path="/test",
            request_id="req123",
            start_time=1234567890000,
            # 可选字段
            error_message="Test error",
            ip_address="192.168.1.1",
            user_agent="Test Agent/1.0",
            end_time=1234567890100,
        )

        assert log.error_message == "Test error"
        assert log.ip_address == "192.168.1.1"
        assert log.user_agent == "Test Agent/1.0"
        assert log.end_time == 1234567890100
