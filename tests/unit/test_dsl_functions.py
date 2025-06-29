"""DSL内置函数单元测试"""

import pytest

from myunla.dsl.functions import (
    _filterActive,
    _filterBy,
    _getNames,
    _length,
    _pluck,
    _toJSON,
    _toNumber,
    _toString,
    get_all_functions,
    get_function,
    register_function,
)
from myunla.dsl.types import DSLValue, DSLValueType


@pytest.mark.unit
@pytest.mark.dsl
class TestDSLFunctions:
    """DSL内置函数测试类"""

    def test_function_registry(self):
        """测试函数注册系统"""
        # 测试获取已注册函数
        assert get_function("toString") is not None
        assert get_function("nonexistent") is None

        # 测试注册新函数
        def test_func():
            return "test"

        register_function("testFunc", test_func)
        assert get_function("testFunc") == test_func

        # 测试获取所有函数
        all_funcs = get_all_functions()
        assert "toString" in all_funcs
        assert "testFunc" in all_funcs

    def test_toString_function(self):
        """测试toString函数"""
        # 数字转字符串
        result = _toString(DSLValue.from_python(42))
        assert result.type == DSLValueType.STRING
        assert result.value == "42"

        # 布尔值转字符串
        result = _toString(DSLValue.from_python(True))
        assert result.value == "true"

        result = _toString(DSLValue.from_python(False))
        assert result.value == "false"

        # null转字符串
        result = _toString(DSLValue.from_python(None))
        assert result.value == ""

        # 数组转字符串
        result = _toString(DSLValue.from_python([1, 2, 3]))
        assert "[" in result.value and "]" in result.value  # 应该包含数组格式

    def test_toNumber_function(self):
        """测试toNumber函数"""
        # 字符串转数字
        result = _toNumber(DSLValue.from_python("123"))
        assert result.type == DSLValueType.NUMBER
        assert result.value == 123

        # 浮点数字符串
        result = _toNumber(DSLValue.from_python("3.14"))
        assert result.value == 3.14

        # 布尔值转数字
        result = _toNumber(DSLValue.from_python(True))
        assert result.value == 1

        result = _toNumber(DSLValue.from_python(False))
        assert result.value == 0

        # 无效字符串
        result = _toNumber(DSLValue.from_python("invalid"))
        assert result.value == 0

    def test_toJSON_function(self):
        """测试toJSON函数"""
        # 对象转JSON
        data = {"name": "Alice", "age": 30}
        result = _toJSON(DSLValue.from_python(data))
        assert result.type == DSLValueType.STRING
        assert '"name"' in result.value
        assert '"Alice"' in result.value

    def test_length_function(self):
        """测试length函数"""
        # 数组长度
        result = _length(DSLValue.from_python([1, 2, 3, 4, 5]))
        assert result.value == 5

        # 字符串长度
        result = _length(DSLValue.from_python("hello"))
        assert result.value == 5

        # 对象长度
        result = _length(DSLValue.from_python({"a": 1, "b": 2}))
        assert result.value == 2

        # 其他类型
        result = _length(DSLValue.from_python(42))
        assert result.value == 0

    def test_filterBy_function(self):
        """测试filterBy函数"""
        users = [
            {"name": "Alice", "age": 30, "active": True},
            {"name": "Bob", "age": 25, "active": False},
            {"name": "Charlie", "age": 35, "active": True},
        ]

        # 按active属性过滤（真值）
        result = _filterBy(
            DSLValue.from_python(users), DSLValue.from_python("active")
        )
        assert len(result.value) == 2
        assert result.value[0]["name"] == "Alice"
        assert result.value[1]["name"] == "Charlie"

        # 按确切值过滤
        result = _filterBy(
            DSLValue.from_python(users),
            DSLValue.from_python("active"),
            DSLValue.from_python(False),
        )
        assert len(result.value) == 1
        assert result.value[0]["name"] == "Bob"

    def test_pluck_function(self):
        """测试pluck函数"""
        users = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35},
        ]

        # 提取名字
        result = _pluck(
            DSLValue.from_python(users), DSLValue.from_python("name")
        )
        assert result.value == ["Alice", "Bob", "Charlie"]

        # 提取年龄
        result = _pluck(
            DSLValue.from_python(users), DSLValue.from_python("age")
        )
        assert result.value == [30, 25, 35]

    def test_filterActive_function(self):
        """测试filterActive函数"""
        users = [
            {"name": "Alice", "active": True},
            {"name": "Bob", "active": False},
            {"name": "Charlie", "active": True},
        ]

        result = _filterActive(DSLValue.from_python(users))
        assert len(result.value) == 2
        assert result.value[0]["name"] == "Alice"
        assert result.value[1]["name"] == "Charlie"

    def test_getNames_function(self):
        """测试getNames函数"""
        users = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35},
        ]

        result = _getNames(DSLValue.from_python(users))
        assert result.value == ["Alice", "Bob", "Charlie"]

    def test_edge_cases(self):
        """测试边界情况"""
        # 空数组
        result = _filterBy(
            DSLValue.from_python([]), DSLValue.from_python("active")
        )
        assert result.value == []

        # 非数组输入
        result = _filterBy(
            DSLValue.from_python("not an array"), DSLValue.from_python("active")
        )
        assert result.value == []

        # 无效属性名
        result = _pluck(
            DSLValue.from_python([{"name": "Alice"}]),
            DSLValue.from_python(123),  # 非字符串属性名
        )
        assert result.value == []
