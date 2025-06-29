"""DSL解析器单元测试"""

import pytest

from myunla.dsl.parser import DSLParser, ParseError
from myunla.dsl.types import (
    ArrayLiteralNode,
    BinaryOperationNode,
    ConditionalNode,
    FunctionCallNode,
    IdentifierNode,
    LiteralNode,
    MemberAccessNode,
    ObjectLiteralNode,
    PipeNode,
    UnaryOperationNode,
)


@pytest.mark.unit
@pytest.mark.dsl
class TestDSLParser:
    """DSL解析器测试类"""

    def setup_method(self):
        """测试方法设置"""
        self.parser = DSLParser()

    def test_parse_literals(self):
        """测试字面量解析"""
        # 数字
        ast = self.parser.parse("42")
        assert isinstance(ast, LiteralNode)
        assert ast.value == 42

        # 字符串
        ast = self.parser.parse('"hello"')
        assert isinstance(ast, LiteralNode)
        assert ast.value == "hello"

        # 布尔值
        ast = self.parser.parse("true")
        assert isinstance(ast, LiteralNode)
        assert ast.value is True

        # null
        ast = self.parser.parse("null")
        assert isinstance(ast, LiteralNode)
        assert ast.value is None

    def test_parse_identifiers(self):
        """测试标识符解析"""
        ast = self.parser.parse("userName")
        assert isinstance(ast, IdentifierNode)
        assert ast.name == "userName"

    def test_parse_binary_operations(self):
        """测试二元操作解析"""
        # 算术运算
        ast = self.parser.parse("a + b")
        assert isinstance(ast, BinaryOperationNode)
        assert ast.operator == "+"
        assert isinstance(ast.left, IdentifierNode)
        assert isinstance(ast.right, IdentifierNode)

        # 比较运算
        ast = self.parser.parse("x > 10")
        assert isinstance(ast, BinaryOperationNode)
        assert ast.operator == ">"

        # 逻辑运算
        ast = self.parser.parse("a && b")
        assert isinstance(ast, BinaryOperationNode)
        assert ast.operator == "&&"

    def test_parse_unary_operations(self):
        """测试一元操作解析"""
        # 负号
        ast = self.parser.parse("-x")
        assert isinstance(ast, UnaryOperationNode)
        assert ast.operator == "-"
        assert isinstance(ast.operand, IdentifierNode)

        # 逻辑非
        ast = self.parser.parse("!flag")
        assert isinstance(ast, UnaryOperationNode)
        assert ast.operator == "!"

    def test_parse_member_access(self):
        """测试成员访问解析"""
        # 点访问
        ast = self.parser.parse("user.name")
        assert isinstance(ast, MemberAccessNode)
        assert isinstance(ast.object, IdentifierNode)
        assert ast.property == "name"
        assert not ast.computed

        # 计算访问
        ast = self.parser.parse("items[0]")
        assert isinstance(ast, MemberAccessNode)
        assert isinstance(ast.object, IdentifierNode)
        assert isinstance(ast.property, LiteralNode)
        assert ast.computed

    def test_parse_function_calls(self):
        """测试函数调用解析"""
        ast = self.parser.parse("length(array)")
        assert isinstance(ast, FunctionCallNode)
        assert isinstance(ast.function, IdentifierNode)
        assert len(ast.arguments) == 1
        assert isinstance(ast.arguments[0], IdentifierNode)

        # 多参数函数
        ast = self.parser.parse("substring(text, 0, 5)")
        assert isinstance(ast, FunctionCallNode)
        assert len(ast.arguments) == 3

    def test_parse_conditional_expressions(self):
        """测试条件表达式解析"""
        ast = self.parser.parse('x > 0 ? "positive" : "negative"')
        assert isinstance(ast, ConditionalNode)
        assert isinstance(ast.condition, BinaryOperationNode)
        assert isinstance(ast.true_expr, LiteralNode)
        assert isinstance(ast.false_expr, LiteralNode)

    def test_parse_array_literals(self):
        """测试数组字面量解析"""
        ast = self.parser.parse("[1, 2, 3]")
        assert isinstance(ast, ArrayLiteralNode)
        assert len(ast.elements) == 3
        assert all(isinstance(elem, LiteralNode) for elem in ast.elements)

        # 空数组
        ast = self.parser.parse("[]")
        assert isinstance(ast, ArrayLiteralNode)
        assert len(ast.elements) == 0

    def test_parse_object_literals(self):
        """测试对象字面量解析"""
        ast = self.parser.parse('{"name": "Alice", "age": 30}')
        assert isinstance(ast, ObjectLiteralNode)
        assert len(ast.properties) == 2

        keys = [prop[0] for prop in ast.properties]
        assert "name" in keys
        assert "age" in keys

    def test_parse_pipe_operations(self):
        """测试管道操作解析"""
        ast = self.parser.parse("data | length(data)")
        assert isinstance(ast, PipeNode)
        assert isinstance(ast.left, IdentifierNode)
        assert isinstance(ast.right, FunctionCallNode)

    def test_parse_complex_expression(self):
        """测试复杂表达式解析"""
        expression = 'user.age >= 18 ? "adult" : "minor"'
        ast = self.parser.parse(expression)
        assert isinstance(ast, ConditionalNode)

        # 条件部分
        condition = ast.condition
        assert isinstance(condition, BinaryOperationNode)
        assert condition.operator == ">="
        assert isinstance(condition.left, MemberAccessNode)

    def test_operator_precedence(self):
        """测试操作符优先级"""
        # 乘法优先于加法
        ast = self.parser.parse("2 + 3 * 4")
        assert isinstance(ast, BinaryOperationNode)
        assert ast.operator == "+"
        assert isinstance(ast.right, BinaryOperationNode)
        assert ast.right.operator == "*"

        # 括号改变优先级
        ast = self.parser.parse("(2 + 3) * 4")
        assert isinstance(ast, BinaryOperationNode)
        assert ast.operator == "*"
        assert isinstance(ast.left, BinaryOperationNode)
        assert ast.left.operator == "+"

    def test_parse_errors(self):
        """测试解析错误"""
        # 不完整的表达式
        with pytest.raises(ParseError):
            self.parser.parse("x +")

        # 不匹配的括号
        with pytest.raises(ParseError):
            self.parser.parse("(x + y")

        # 不完整的数组
        with pytest.raises(ParseError):
            self.parser.parse("[1, 2,")

        # 不完整的对象
        with pytest.raises(ParseError):
            self.parser.parse('{"key":}')

    def test_associativity(self):
        """测试操作符结合性"""
        # 左结合
        ast = self.parser.parse("a - b - c")
        assert isinstance(ast, BinaryOperationNode)
        assert ast.operator == "-"
        assert isinstance(ast.left, BinaryOperationNode)
        assert ast.left.operator == "-"

    def test_chained_member_access(self):
        """测试链式成员访问"""
        ast = self.parser.parse("user.profile.name")
        assert isinstance(ast, MemberAccessNode)
        assert ast.property == "name"
        assert isinstance(ast.object, MemberAccessNode)
        assert ast.object.property == "profile"
