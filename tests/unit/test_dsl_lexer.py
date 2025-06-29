"""DSL词法分析器单元测试"""

import pytest

from myunla.dsl.lexer import DSLLexer, TokenType


@pytest.mark.unit
@pytest.mark.dsl
class TestDSLLexer:
    """DSL词法分析器测试类"""

    def setup_method(self):
        """测试方法设置"""
        self.lexer = DSLLexer()

    def test_tokenize_numbers(self):
        """测试数字token化"""
        tokens = self.lexer.tokenize("42 3.14")
        assert len(tokens) == 3  # 2 numbers + EOF
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"
        assert tokens[1].type == TokenType.NUMBER
        assert tokens[1].value == "3.14"

    def test_tokenize_strings(self):
        """测试字符串token化"""
        tokens = self.lexer.tokenize('"hello" \'world\'')
        assert len(tokens) == 3  # 2 strings + EOF
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == '"hello"'
        assert tokens[1].type == TokenType.STRING
        assert tokens[1].value == "'world'"

    def test_tokenize_identifiers(self):
        """测试标识符token化"""
        tokens = self.lexer.tokenize("user name _private")
        assert len(tokens) == 4  # 3 identifiers + EOF
        assert all(token.type == TokenType.IDENTIFIER for token in tokens[:3])
        assert tokens[0].value == "user"
        assert tokens[1].value == "name"
        assert tokens[2].value == "_private"

    def test_tokenize_keywords(self):
        """测试关键词token化"""
        tokens = self.lexer.tokenize("true false null if else")
        expected_types = [
            TokenType.BOOLEAN,
            TokenType.BOOLEAN,
            TokenType.NULL,
            TokenType.IF,
            TokenType.ELSE,
            TokenType.EOF,
        ]
        assert len(tokens) == len(expected_types)
        for token, expected_type in zip(tokens, expected_types):
            assert token.type == expected_type

    def test_tokenize_operators(self):
        """测试操作符token化"""
        tokens = self.lexer.tokenize("+ - * / % == != < > <= >= && ||")
        expected_types = [
            TokenType.PLUS,
            TokenType.MINUS,
            TokenType.MULTIPLY,
            TokenType.DIVIDE,
            TokenType.MODULO,
            TokenType.EQUAL,
            TokenType.NOT_EQUAL,
            TokenType.LESS_THAN,
            TokenType.GREATER_THAN,
            TokenType.LESS_EQUAL,
            TokenType.GREATER_EQUAL,
            TokenType.AND,
            TokenType.OR,
            TokenType.EOF,
        ]
        assert len(tokens) == len(expected_types)
        for token, expected_type in zip(tokens, expected_types):
            assert token.type == expected_type

    def test_tokenize_punctuation(self):
        """测试标点符号token化"""
        tokens = self.lexer.tokenize("() [] {} . , ; ? : |")
        expected_types = [
            TokenType.LEFT_PAREN,
            TokenType.RIGHT_PAREN,
            TokenType.LEFT_BRACKET,
            TokenType.RIGHT_BRACKET,
            TokenType.LEFT_BRACE,
            TokenType.RIGHT_BRACE,
            TokenType.DOT,
            TokenType.COMMA,
            TokenType.SEMICOLON,
            TokenType.QUESTION,
            TokenType.COLON,
            TokenType.PIPE,
            TokenType.EOF,
        ]
        assert len(tokens) == len(expected_types)
        for token, expected_type in zip(tokens, expected_types):
            assert token.type == expected_type

    def test_tokenize_complex_expression(self):
        """测试复杂表达式token化"""
        expression = 'user.name + " (" + toString(user.age) + ")"'
        tokens = self.lexer.tokenize(expression)

        # 验证token序列
        expected_sequence = [
            (TokenType.IDENTIFIER, "user"),
            (TokenType.DOT, "."),
            (TokenType.IDENTIFIER, "name"),
            (TokenType.PLUS, "+"),
            (TokenType.STRING, '" ("'),
            (TokenType.PLUS, "+"),
            (TokenType.IDENTIFIER, "toString"),
            (TokenType.LEFT_PAREN, "("),
            (TokenType.IDENTIFIER, "user"),
            (TokenType.DOT, "."),
            (TokenType.IDENTIFIER, "age"),
            (TokenType.RIGHT_PAREN, ")"),
            (TokenType.PLUS, "+"),
            (TokenType.STRING, '")"'),
            (TokenType.EOF, ""),
        ]

        assert len(tokens) == len(expected_sequence)
        for token, (expected_type, expected_value) in zip(
            tokens, expected_sequence
        ):
            assert token.type == expected_type
            if expected_value:
                assert token.value == expected_value

    def test_position_tracking(self):
        """测试位置跟踪"""
        tokens = self.lexer.tokenize("hello\nworld")

        # 第一个token在第1行
        assert tokens[0].line == 1
        assert tokens[0].column == 1

        # 第二个token在第2行
        assert tokens[1].line == 2
        assert tokens[1].column == 1

    def test_whitespace_handling(self):
        """测试空白字符处理"""
        tokens = self.lexer.tokenize("  hello   world  ")
        # 空白字符应该被过滤掉
        assert len(tokens) == 3  # hello, world, EOF
        assert tokens[0].value == "hello"
        assert tokens[1].value == "world"

    def test_empty_input(self):
        """测试空输入"""
        tokens = self.lexer.tokenize("")
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF
