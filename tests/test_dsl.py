"""DSL完整功能测试 - 重构后的集成测试"""

import pytest

from myunla.dsl import parse_and_execute, validate_expression


def test_basic_expressions():
    """Test basic expression parsing and execution."""
    context = {"x": 10, "y": 20}

    # Test literals
    assert parse_and_execute("42", context).value == 42
    assert parse_and_execute('"hello"', context).value == "hello"
    assert parse_and_execute("true", context).value
    assert parse_and_execute("null", context).value is None

    # Test variable access
    assert parse_and_execute("x", context).value == 10
    assert parse_and_execute("y", context).value == 20


def test_arithmetic_operations():
    """Test arithmetic operations."""
    context = {"a": 5, "b": 3}

    assert parse_and_execute("a + b", context).value == 8
    assert parse_and_execute("a - b", context).value == 2
    assert parse_and_execute("a * b", context).value == 15
    assert parse_and_execute("a / b", context).value == 5 / 3
    assert parse_and_execute("a % b", context).value == 2


def test_string_operations():
    """Test string operations."""
    context = {"name": "Alice", "greeting": "Hello"}

    result = parse_and_execute('greeting + " " + name', context)
    assert result.value == "Hello Alice"

    result = parse_and_execute('"Hello" * 3', context)
    assert result.value == "HelloHelloHello"


def test_comparison_operations():
    """Test comparison operations."""
    context = {"a": 5, "b": 3}

    assert parse_and_execute("a > b", context).value
    assert not parse_and_execute("a < b", context).value
    assert parse_and_execute("a == 5", context).value
    assert parse_and_execute("a != b", context).value


def test_logical_operations():
    """Test logical operations."""
    context = {"x": True, "y": False}

    assert not parse_and_execute("x && y", context).value
    assert parse_and_execute("x || y", context).value
    assert not parse_and_execute("!x", context).value
    assert parse_and_execute("!y", context).value


def test_conditional_expressions():
    """Test conditional (ternary) expressions."""
    context = {"age": 25, "isAdmin": True}

    result = parse_and_execute('age >= 18 ? "adult" : "minor"', context)
    assert result.value == "adult"

    result = parse_and_execute('isAdmin ? "admin" : "user"', context)
    assert result.value == "admin"


def test_member_access():
    """Test object member access."""
    context = {"user": {"name": "Alice", "age": 30}, "items": [1, 2, 3, 4, 5]}

    assert parse_and_execute("user.name", context).value == "Alice"
    assert parse_and_execute("user.age", context).value == 30
    assert parse_and_execute("items[0]", context).value == 1
    assert parse_and_execute("items[2]", context).value == 3


def test_array_literals():
    """Test array literal construction."""
    context = {"x": 1, "y": 2}

    result = parse_and_execute("[1, 2, 3]", context)
    assert result.value == [1, 2, 3]

    result = parse_and_execute("[x, y, x + y]", context)
    assert result.value == [1, 2, 3]


def test_object_literals():
    """Test object literal construction."""
    context = {"name": "Alice", "age": 30}

    result = parse_and_execute('{"x": 1, "y": 2}', context)
    assert result.value == {"x": 1, "y": 2}

    result = parse_and_execute('{"name": name, "age": age}', context)
    assert result.value == {"name": "Alice", "age": 30}


def test_builtin_functions():
    """Test built-in functions."""
    context = {
        "text": "hello world",
        "numbers": [3, 1, 4, 1, 5],
        "user": {"name": "Alice", "email": "alice@example.com"},
    }

    # String functions
    assert parse_and_execute('length(text)', context).value == 11

    # Array functions
    assert parse_and_execute('length(numbers)', context).value == 5

    # Type conversion
    result = parse_and_execute('toString(42)', context)
    assert result.value == "42"

    result = parse_and_execute('toNumber("123")', context)
    assert result.value == 123


def test_pipe_operations():
    """Test pipe operations."""
    context = {"data": [1, 2, 3, 4, 5]}

    # Note: This test would need lambda function support
    # For now, just test basic piping
    result = parse_and_execute('data | length(data)', context)
    assert result.value == 5


def test_error_handling():
    """Test error handling."""
    context = {}

    # Division by zero
    result = parse_and_execute("1 / 0", context)
    assert not result.success
    assert "Division by zero" in result.error.message

    # Undefined variable (should return null gracefully)
    result = parse_and_execute("undefined_var", context)
    assert result.success
    assert result.value is None


def test_validation():
    """Test expression validation."""

    # Valid expressions
    valid_expressions = [
        "42",
        "x + y",
        "user.name",
        '[1, 2, 3]',
        '{"key": "value"}',
        'x > 0 ? "positive" : "non-positive"',
    ]

    for expr in valid_expressions:
        result = validate_expression(expr)
        assert result.success, f"Expression '{expr}' should be valid"

    # Invalid expressions
    invalid_expressions = [
        "x +",  # Incomplete expression
        "user.",  # Incomplete member access
        "[1, 2,",  # Incomplete array
        '{"key":}',  # Incomplete object
    ]

    for expr in invalid_expressions:
        result = validate_expression(expr)
        assert not result.success, f"Expression '{expr}' should be invalid"


def test_complex_scenarios():
    """Test complex real-world scenarios."""

    # API URL building
    context = {
        "config": {"baseUrl": "https://api.example.com"},
        "args": {"userId": "123", "format": "json"},
    }

    result = parse_and_execute(
        'config.baseUrl + "/users/" + args.userId + "?format=" + args.format',
        context,
    )
    assert result.value == "https://api.example.com/users/123?format=json"

    # Conditional headers
    context = {
        "config": {"apiKey": "secret123"},
        "request": {"headers": {"Authorization": "Bearer token"}},
    }

    result = parse_and_execute(
        '{"Content-Type": "application/json", "Authorization": request.headers.Authorization}',
        context,
    )
    expected = {
        "Content-Type": "application/json",
        "Authorization": "Bearer token",
    }
    assert result.value == expected


if __name__ == "__main__":
    pytest.main([__file__])
