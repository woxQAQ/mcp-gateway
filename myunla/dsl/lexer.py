"""Lexer for the API Template DSL."""

import re
from enum import Enum
from typing import NamedTuple, Optional


class TokenType(Enum):
    """Token types for the DSL."""

    # Literals
    NUMBER = "NUMBER"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    NULL = "NULL"

    # Identifiers
    IDENTIFIER = "IDENTIFIER"

    # Operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    MODULO = "MODULO"

    # Comparison
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_EQUAL = "LESS_EQUAL"
    GREATER_THAN = "GREATER_THAN"
    GREATER_EQUAL = "GREATER_EQUAL"

    # Logical
    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    # Assignment
    ASSIGN = "ASSIGN"

    # Punctuation
    DOT = "DOT"
    COMMA = "COMMA"
    SEMICOLON = "SEMICOLON"
    QUESTION = "QUESTION"
    COLON = "COLON"
    PIPE = "PIPE"

    # Brackets
    LEFT_PAREN = "LEFT_PAREN"
    RIGHT_PAREN = "RIGHT_PAREN"
    LEFT_BRACKET = "LEFT_BRACKET"
    RIGHT_BRACKET = "RIGHT_BRACKET"
    LEFT_BRACE = "LEFT_BRACE"
    RIGHT_BRACE = "RIGHT_BRACE"

    # Keywords
    IF = "IF"
    ELSE = "ELSE"
    FOR = "FOR"
    IN = "IN"
    LET = "LET"
    FUNCTION = "FUNCTION"
    RETURN = "RETURN"

    # Special
    EOF = "EOF"
    NEWLINE = "NEWLINE"
    WHITESPACE = "WHITESPACE"


class Token(NamedTuple):
    """Represents a token in the DSL."""

    type: TokenType
    value: str
    position: int
    line: int
    column: int


class LexerError(Exception):
    """Lexer error."""

    def __init__(self, message: str, position: int, line: int, column: int):
        super().__init__(message)
        self.position = position
        self.line = line
        self.column = column


class DSLLexer:
    """Lexer for the API Template DSL."""

    # Token patterns
    TOKEN_PATTERNS = [
        # Numbers (integers and floats)
        (r'\d+\.\d+', TokenType.NUMBER),
        (r'\d+', TokenType.NUMBER),
        # Strings (single and double quoted)
        (r'"([^"\\]|\\.)*"', TokenType.STRING),
        (r"'([^'\\]|\\.)*'", TokenType.STRING),
        # Boolean and null
        (r'\btrue\b', TokenType.BOOLEAN),
        (r'\bfalse\b', TokenType.BOOLEAN),
        (r'\bnull\b', TokenType.NULL),
        # Keywords
        (r'\bif\b', TokenType.IF),
        (r'\belse\b', TokenType.ELSE),
        (r'\bfor\b', TokenType.FOR),
        (r'\bin\b', TokenType.IN),
        (r'\blet\b', TokenType.LET),
        (r'\bfunction\b', TokenType.FUNCTION),
        (r'\breturn\b', TokenType.RETURN),
        # Multi-character operators
        (r'==', TokenType.EQUAL),
        (r'!=', TokenType.NOT_EQUAL),
        (r'<=', TokenType.LESS_EQUAL),
        (r'>=', TokenType.GREATER_EQUAL),
        (r'&&', TokenType.AND),
        (r'\|\|', TokenType.OR),
        # Single-character operators
        (r'\+', TokenType.PLUS),
        (r'-', TokenType.MINUS),
        (r'\*', TokenType.MULTIPLY),
        (r'/', TokenType.DIVIDE),
        (r'%', TokenType.MODULO),
        (r'<', TokenType.LESS_THAN),
        (r'>', TokenType.GREATER_THAN),
        (r'!', TokenType.NOT),
        (r'=', TokenType.ASSIGN),
        # Punctuation
        (r'\.', TokenType.DOT),
        (r',', TokenType.COMMA),
        (r';', TokenType.SEMICOLON),
        (r'\?', TokenType.QUESTION),
        (r':', TokenType.COLON),
        (r'\|', TokenType.PIPE),
        # Brackets
        (r'\(', TokenType.LEFT_PAREN),
        (r'\)', TokenType.RIGHT_PAREN),
        (r'\[', TokenType.LEFT_BRACKET),
        (r'\]', TokenType.RIGHT_BRACKET),
        (r'\{', TokenType.LEFT_BRACE),
        (r'\}', TokenType.RIGHT_BRACE),
        # Identifiers (must come after keywords)
        (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENTIFIER),
        # Whitespace and newlines
        (r'\n', TokenType.NEWLINE),
        (r'[ \t\r]+', TokenType.WHITESPACE),
    ]

    def __init__(self):
        self.text = ""
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

        # Compile patterns
        self.compiled_patterns = [
            (re.compile(pattern), token_type)
            for pattern, token_type in self.TOKEN_PATTERNS
        ]

    def tokenize(self, text: str) -> list[Token]:
        """Tokenize the input text."""
        self.text = text
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []

        while self.position < len(self.text):
            self._skip_whitespace_and_comments()

            if self.position >= len(self.text):
                break

            token = self._read_next_token()
            if token:
                # Skip whitespace tokens in the output
                if token.type not in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    self.tokens.append(token)

        # Add EOF token
        self.tokens.append(
            Token(TokenType.EOF, "", self.position, self.line, self.column)
        )

        return self.tokens

    def _skip_whitespace_and_comments(self):
        """Skip whitespace and comments."""
        while self.position < len(self.text):
            # Skip regular whitespace
            if self.text[self.position].isspace():
                if self.text[self.position] == '\n':
                    self.line += 1
                    self.column = 1
                else:
                    self.column += 1
                self.position += 1
                continue

            # Skip line comments (//)
            if (
                self.position < len(self.text) - 1
                and self.text[self.position : self.position + 2] == '//'
            ):
                while (
                    self.position < len(self.text)
                    and self.text[self.position] != '\n'
                ):
                    self.position += 1
                continue

            # Skip block comments (/* */)
            if (
                self.position < len(self.text) - 1
                and self.text[self.position : self.position + 2] == '/*'
            ):
                self.position += 2
                while self.position < len(self.text) - 1:
                    if self.text[self.position : self.position + 2] == '*/':
                        self.position += 2
                        break
                    if self.text[self.position] == '\n':
                        self.line += 1
                        self.column = 1
                    else:
                        self.column += 1
                    self.position += 1
                continue

            break

    def _read_next_token(self) -> Optional[Token]:
        """Read the next token from the input."""
        if self.position >= len(self.text):
            return None

        # Try to match each pattern
        for pattern, token_type in self.compiled_patterns:
            match = pattern.match(self.text, self.position)
            if match:
                value = match.group(0)
                token = Token(
                    token_type, value, self.position, self.line, self.column
                )

                # Update position
                self.position = match.end()
                self.column += len(value)

                return token

        # No pattern matched
        char = self.text[self.position]
        raise LexerError(
            f"Unexpected character: '{char}'",
            self.position,
            self.line,
            self.column,
        )

    def peek_token(self, offset: int = 0) -> Optional[Token]:
        """Peek at a token without consuming it."""
        if offset < len(self.tokens):
            return self.tokens[offset]
        return None

    def current_token(self) -> Optional[Token]:
        """Get the current token."""
        return self.peek_token(0)
