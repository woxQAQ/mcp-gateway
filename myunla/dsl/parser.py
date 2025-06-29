"""Parser for the API Template DSL."""

from typing import Optional

from myunla.dsl.lexer import DSLLexer, Token, TokenType
from myunla.dsl.types import (
    ArrayLiteralNode,
    ASTNode,
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


class ParseError(Exception):
    """Parse error."""

    def __init__(self, message: str, token: Optional[Token] = None):
        super().__init__(message)
        self.token = token


class DSLParser:
    """Parser for the API Template DSL."""

    def __init__(self):
        self.lexer = DSLLexer()
        self.tokens: list[Token] = []
        self.current = 0

    def parse(self, text: str) -> ASTNode:
        """Parse DSL text into an AST."""
        self.tokens = self.lexer.tokenize(text)
        self.current = 0

        try:
            return self._parse_expression()
        except IndexError:
            raise ParseError("Unexpected end of input")

    def _current_token(self) -> Token:
        """Get current token."""
        if self.current >= len(self.tokens):
            return self.tokens[-1]  # EOF token
        return self.tokens[self.current]

    def _peek_token(self, offset: int = 1) -> Token:
        """Peek at next token."""
        index = self.current + offset
        if index >= len(self.tokens):
            return self.tokens[-1]  # EOF token
        return self.tokens[index]

    def _advance(self) -> Token:
        """Consume and return current token."""
        token = self._current_token()
        if token.type != TokenType.EOF:
            self.current += 1
        return token

    def _match(self, *types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self._current_token().type in types

    def _consume(self, token_type: TokenType, message: str = None) -> Token:
        """Consume token of expected type or raise error."""
        if self._current_token().type == token_type:
            return self._advance()

        if message is None:
            message = f"Expected {token_type.value}, got {self._current_token().type.value}"

        raise ParseError(message, self._current_token())

    def _parse_expression(self) -> ASTNode:
        """Parse expression (top level)."""
        return self._parse_pipe()

    def _parse_pipe(self) -> ASTNode:
        """Parse pipe expressions (data | function)."""
        expr = self._parse_conditional()

        while self._match(TokenType.PIPE):
            self._advance()  # consume |
            right = self._parse_conditional()
            expr = PipeNode(expr, right)

        return expr

    def _parse_conditional(self) -> ASTNode:
        """Parse conditional expressions (ternary operator)."""
        expr = self._parse_logical_or()

        if self._match(TokenType.QUESTION):
            self._advance()  # consume ?
            true_expr = self._parse_expression()
            self._consume(TokenType.COLON)
            false_expr = self._parse_expression()
            return ConditionalNode(expr, true_expr, false_expr)

        return expr

    def _parse_logical_or(self) -> ASTNode:
        """Parse logical OR expressions."""
        expr = self._parse_logical_and()

        while self._match(TokenType.OR):
            operator = self._advance().value
            right = self._parse_logical_and()
            expr = BinaryOperationNode(expr, operator, right)

        return expr

    def _parse_logical_and(self) -> ASTNode:
        """Parse logical AND expressions."""
        expr = self._parse_equality()

        while self._match(TokenType.AND):
            operator = self._advance().value
            right = self._parse_equality()
            expr = BinaryOperationNode(expr, operator, right)

        return expr

    def _parse_equality(self) -> ASTNode:
        """Parse equality expressions."""
        expr = self._parse_comparison()

        while self._match(TokenType.EQUAL, TokenType.NOT_EQUAL):
            operator = self._advance().value
            right = self._parse_comparison()
            expr = BinaryOperationNode(expr, operator, right)

        return expr

    def _parse_comparison(self) -> ASTNode:
        """Parse comparison expressions."""
        expr = self._parse_addition()

        while self._match(
            TokenType.GREATER_THAN,
            TokenType.GREATER_EQUAL,
            TokenType.LESS_THAN,
            TokenType.LESS_EQUAL,
        ):
            operator = self._advance().value
            right = self._parse_addition()
            expr = BinaryOperationNode(expr, operator, right)

        return expr

    def _parse_addition(self) -> ASTNode:
        """Parse addition and subtraction."""
        expr = self._parse_multiplication()

        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._advance().value
            right = self._parse_multiplication()
            expr = BinaryOperationNode(expr, operator, right)

        return expr

    def _parse_multiplication(self) -> ASTNode:
        """Parse multiplication, division, and modulo."""
        expr = self._parse_unary()

        while self._match(
            TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO
        ):
            operator = self._advance().value
            right = self._parse_unary()
            expr = BinaryOperationNode(expr, operator, right)

        return expr

    def _parse_unary(self) -> ASTNode:
        """Parse unary expressions."""
        if self._match(TokenType.NOT, TokenType.MINUS):
            operator = self._advance().value
            expr = self._parse_unary()
            return UnaryOperationNode(operator, expr)

        return self._parse_member_access()

    def _parse_member_access(self) -> ASTNode:
        """Parse member access and function calls."""
        expr = self._parse_primary()

        while True:
            if self._match(TokenType.DOT):
                self._advance()  # consume .
                name_token = self._consume(TokenType.IDENTIFIER)
                property_name = name_token.value
                expr = MemberAccessNode(expr, property_name, computed=False)

            elif self._match(TokenType.LEFT_BRACKET):
                self._advance()  # consume [
                index = self._parse_expression()
                self._consume(TokenType.RIGHT_BRACKET)
                expr = MemberAccessNode(expr, index, computed=True)

            elif self._match(TokenType.LEFT_PAREN):
                self._advance()  # consume (
                arguments = []

                if not self._match(TokenType.RIGHT_PAREN):
                    arguments.append(self._parse_expression())
                    while self._match(TokenType.COMMA):
                        self._advance()  # consume ,
                        arguments.append(self._parse_expression())

                self._consume(TokenType.RIGHT_PAREN)
                expr = FunctionCallNode(expr, arguments)

            else:
                break

        return expr

    def _parse_primary(self) -> ASTNode:
        """Parse primary expressions."""
        # Numbers
        if self._match(TokenType.NUMBER):
            value = self._advance().value
            if '.' in value:
                return LiteralNode(float(value))
            else:
                return LiteralNode(int(value))

        # Strings
        if self._match(TokenType.STRING):
            value = self._advance().value
            # Remove quotes and handle escape sequences
            unquoted = value[1:-1]  # Remove surrounding quotes
            unquoted = unquoted.replace('\\"', '"').replace("\\'", "'")
            unquoted = unquoted.replace('\\n', '\n').replace('\\t', '\t')
            unquoted = unquoted.replace('\\r', '\r').replace('\\\\', '\\')
            return LiteralNode(unquoted)

        # Booleans
        if self._match(TokenType.BOOLEAN):
            value = self._advance().value
            return LiteralNode(value == 'true')

        # Null
        if self._match(TokenType.NULL):
            self._advance()
            return LiteralNode(None)

        # Identifiers
        if self._match(TokenType.IDENTIFIER):
            name = self._advance().value
            return IdentifierNode(name)

        # Parenthesized expressions
        if self._match(TokenType.LEFT_PAREN):
            self._advance()  # consume (
            expr = self._parse_expression()
            self._consume(TokenType.RIGHT_PAREN)
            return expr

        # Array literals
        if self._match(TokenType.LEFT_BRACKET):
            return self._parse_array_literal()

        # Object literals
        if self._match(TokenType.LEFT_BRACE):
            return self._parse_object_literal()

        raise ParseError(
            f"Unexpected token: {self._current_token().value}",
            self._current_token(),
        )

    def _parse_array_literal(self) -> ArrayLiteralNode:
        """Parse array literal [1, 2, 3]."""
        self._consume(TokenType.LEFT_BRACKET)
        elements = []

        if not self._match(TokenType.RIGHT_BRACKET):
            elements.append(self._parse_expression())
            while self._match(TokenType.COMMA):
                self._advance()  # consume ,
                # Allow trailing commas
                if self._match(TokenType.RIGHT_BRACKET):
                    break
                elements.append(self._parse_expression())

        self._consume(TokenType.RIGHT_BRACKET)
        return ArrayLiteralNode(elements)

    def _parse_object_literal(self) -> ObjectLiteralNode:
        """Parse object literal {key: value, ...}."""
        self._consume(TokenType.LEFT_BRACE)
        properties = []

        if not self._match(TokenType.RIGHT_BRACE):
            # Parse first property
            key, value = self._parse_object_property()
            properties.append((key, value))

            while self._match(TokenType.COMMA):
                self._advance()  # consume ,
                # Allow trailing commas
                if self._match(TokenType.RIGHT_BRACE):
                    break
                key, value = self._parse_object_property()
                properties.append((key, value))

        self._consume(TokenType.RIGHT_BRACE)
        return ObjectLiteralNode(properties)

    def _parse_object_property(self) -> tuple[str, ASTNode]:
        """Parse object property (key: value)."""
        # Key can be identifier or string
        if self._match(TokenType.IDENTIFIER):
            key = self._advance().value
        elif self._match(TokenType.STRING):
            key_token = self._advance()
            key = key_token.value[1:-1]  # Remove quotes
        else:
            raise ParseError("Expected property key", self._current_token())

        self._consume(TokenType.COLON)
        value = self._parse_expression()

        return key, value
