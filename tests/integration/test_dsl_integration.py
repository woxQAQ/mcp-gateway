"""DSL集成测试 - 测试完整的DSL功能流程"""

import pytest

from myunla.dsl import parse_and_execute, validate_expression


@pytest.mark.integration
@pytest.mark.dsl
class TestDSLIntegration:
    """DSL集成测试类"""

    def test_complete_data_transformation_workflow(self, dsl_test_context):
        """测试完整的数据转换工作流"""
        # 获取所有用户
        result = parse_and_execute("users", dsl_test_context)
        assert result.success
        assert len(result.value) == 3

        # 过滤活跃用户
        result = parse_and_execute(
            "users | filterActive(data)", dsl_test_context
        )
        assert result.success
        assert len(result.value) == 2
        active_users = result.value
        assert all(user["active"] for user in active_users)

        # 获取活跃用户姓名
        result = parse_and_execute(
            "users | filterActive(data) | getNames(data)", dsl_test_context
        )
        assert result.success
        assert result.value == ["Alice", "Charlie"]

        # 连接姓名为字符串
        result = parse_and_execute(
            'users | filterActive(data) | getNames(data) | join(data, ", ")',
            dsl_test_context,
        )
        assert result.success
        assert result.value == "Alice, Charlie"

    def test_api_url_building_workflow(self, dsl_test_context):
        """测试API URL构建工作流"""
        # 基本URL构建
        result = parse_and_execute(
            'config.baseUrl + "/users"', dsl_test_context
        )
        assert result.success
        assert result.value == "https://api.example.com/users"

        # 带参数的URL构建
        result = parse_and_execute(
            'config.baseUrl + "/users/" + args.userId + "?format=" + args.format',
            dsl_test_context,
        )
        assert result.success
        assert result.value == "https://api.example.com/users/123?format=json"

        # 动态URL构建
        result = parse_and_execute(
            'user.age >= 18 ? config.baseUrl + "/adult" : config.baseUrl + "/minor"',
            dsl_test_context,
        )
        assert result.success
        assert result.value == "https://api.example.com/adult"

    def test_complex_conditional_logic(self, dsl_test_context):
        """测试复杂的条件逻辑"""
        # 嵌套条件
        result = parse_and_execute(
            'user.age >= 18 ? (user.active ? "active_adult" : "inactive_adult") : "minor"',
            dsl_test_context,
        )
        assert result.success
        assert result.value == "active_adult"

        # 多重比较
        result = parse_and_execute(
            'user.age >= 18 && user.age < 65 && user.active', dsl_test_context
        )
        assert result.success
        assert result.value is True

    def test_array_manipulation_chain(self, dsl_test_context):
        """测试数组操作链"""
        # 数组长度
        result = parse_and_execute("numbers | length(data)", dsl_test_context)
        assert result.success
        assert result.value == 5

        # 数组索引访问
        result = parse_and_execute("numbers[0]", dsl_test_context)
        assert result.success
        assert result.value == 1

        result = parse_and_execute("numbers[4]", dsl_test_context)
        assert result.success
        assert result.value == 5

    def test_object_property_access_chain(self, dsl_test_context):
        """测试对象属性访问链"""
        # 深层属性访问
        nested_context = {
            "user": {"profile": {"personal": {"name": "Alice", "age": 30}}}
        }

        result = parse_and_execute("user.profile.personal.name", nested_context)
        assert result.success
        assert result.value == "Alice"

        result = parse_and_execute("user.profile.personal.age", nested_context)
        assert result.success
        assert result.value == 30

    def test_type_conversion_workflow(self, dsl_test_context):
        """测试类型转换工作流"""
        # 数字转字符串
        result = parse_and_execute("toString(user.age)", dsl_test_context)
        assert result.success
        assert result.value == "30"

        # 字符串转数字
        string_context = {"ageStr": "25"}
        result = parse_and_execute("toNumber(ageStr)", string_context)
        assert result.success
        assert result.value == 25

        # 布尔值转字符串
        result = parse_and_execute("toString(user.active)", dsl_test_context)
        assert result.success
        assert result.value == "true"

    def test_error_recovery_and_validation(self):
        """测试错误恢复和验证"""
        # 无效表达式应该返回失败
        result = parse_and_execute("invalid + syntax +", {})
        assert not result.success
        assert result.error is not None

        # 验证应该捕获语法错误
        validation = validate_expression("incomplete [")
        assert not validation.success

        # 运行时错误处理
        result = parse_and_execute("1 / 0", {})
        assert not result.success
        assert "Division by zero" in result.error.message

    def test_real_world_api_template_scenario(self):
        """测试真实世界的API模板场景"""
        api_context = {
            "request": {
                "method": "POST",
                "headers": {"Authorization": "Bearer token123"},
                "body": {"name": "New User", "email": "new@example.com"},
            },
            "config": {
                "apiUrl": "https://api.service.com",
                "timeout": 30,
                "retries": 3,
            },
            "user": {
                "id": "user456",
                "role": "admin",
                "permissions": ["read", "write", "delete"],
            },
        }

        # 构建请求URL
        result = parse_and_execute('config.apiUrl + "/users"', api_context)
        assert result.success
        assert result.value == "https://api.service.com/users"

        # 条件性权限检查
        result = parse_and_execute(
            'user.role == "admin" ? "allowed" : "denied"', api_context
        )
        assert result.success
        assert result.value == "allowed"

        # 构建请求头
        result = parse_and_execute('request.headers.Authorization', api_context)
        assert result.success
        assert result.value == "Bearer token123"

    def test_performance_with_large_data(self):
        """测试大数据量的性能"""
        # 创建大量数据
        large_data = {
            "items": [{"id": i, "active": i % 2 == 0} for i in range(1000)]
        }

        # 过滤大量数据
        result = parse_and_execute(
            'items | filterBy(data, "active", true) | length(data)', large_data
        )
        assert result.success
        assert result.value == 500  # 一半是active的

    def test_nested_function_calls(self, dsl_test_context):
        """测试嵌套函数调用"""
        # 嵌套的toString和length调用
        result = parse_and_execute('toString(length(users))', dsl_test_context)
        assert result.success
        assert result.value == "3"

        # 复杂的嵌套调用
        result = parse_and_execute(
            'length(toString(user.age))', dsl_test_context
        )
        assert result.success
        assert result.value == 2  # "30"的长度

    def test_edge_cases_and_boundary_conditions(self):
        """测试边界条件和特殊情况"""
        # 空数据
        result = parse_and_execute("[]", {})
        assert result.success
        assert result.value == []

        # 空对象
        result = parse_and_execute("{}", {})
        assert result.success
        assert result.value == {}

        # null值处理
        result = parse_and_execute("null", {})
        assert result.success
        assert result.value is None

        # 未定义变量（应返回null）
        result = parse_and_execute("undefined_variable", {})
        assert result.success
        assert result.value is None
