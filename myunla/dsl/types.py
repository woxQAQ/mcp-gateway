"""Type definitions for the API Template DSL."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class DSLValueType(Enum):
    """DSL value types."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"
    FUNCTION = "function"


@dataclass
class DSLValue:
    """Represents a value in the DSL."""

    value: Any
    type: DSLValueType

    @classmethod
    def from_python(cls, value: Any) -> 'DSLValue':
        """Convert Python value to DSLValue."""
        if value is None:
            return cls(None, DSLValueType.NULL)
        elif isinstance(value, bool):
            return cls(value, DSLValueType.BOOLEAN)
        elif isinstance(value, (int, float)):
            return cls(value, DSLValueType.NUMBER)
        elif isinstance(value, str):
            return cls(value, DSLValueType.STRING)
        elif isinstance(value, list):
            return cls(value, DSLValueType.ARRAY)
        elif isinstance(value, dict):
            return cls(value, DSLValueType.OBJECT)
        elif callable(value):
            return cls(value, DSLValueType.FUNCTION)
        else:
            return cls(str(value), DSLValueType.STRING)

    def to_python(self) -> Any:
        """Convert DSLValue to Python value."""
        return self.value

    def is_truthy(self) -> bool:
        """Check if value is truthy."""
        if self.type == DSLValueType.NULL:
            return False
        elif self.type == DSLValueType.BOOLEAN:
            return self.value
        elif self.type == DSLValueType.NUMBER:
            return self.value != 0
        elif self.type == DSLValueType.STRING:
            return len(self.value) > 0
        elif self.type == DSLValueType.ARRAY:
            return len(self.value) > 0
        elif self.type == DSLValueType.OBJECT:
            return len(self.value) > 0
        return True


@dataclass
class DSLError:
    """Represents an error in DSL execution."""

    message: str
    code: str
    position: Optional[int] = None
    context: Optional[str] = None


@dataclass
class DSLResult:
    """Result of DSL execution."""

    success: bool
    value: Any = None
    error: Optional[DSLError] = None


class ASTNode(ABC):
    """Base class for AST nodes."""

    @abstractmethod
    def accept(self, visitor: 'ASTVisitor') -> DSLValue:
        pass


class ASTVisitor(ABC):
    """Visitor interface for AST traversal."""

    @abstractmethod
    def visit_literal(self, node: 'LiteralNode') -> DSLValue:
        pass

    @abstractmethod
    def visit_identifier(self, node: 'IdentifierNode') -> DSLValue:
        pass

    @abstractmethod
    def visit_member_access(self, node: 'MemberAccessNode') -> DSLValue:
        pass

    @abstractmethod
    def visit_function_call(self, node: 'FunctionCallNode') -> DSLValue:
        pass

    @abstractmethod
    def visit_binary_operation(self, node: 'BinaryOperationNode') -> DSLValue:
        pass

    @abstractmethod
    def visit_unary_operation(self, node: 'UnaryOperationNode') -> DSLValue:
        pass

    @abstractmethod
    def visit_conditional(self, node: 'ConditionalNode') -> DSLValue:
        pass

    @abstractmethod
    def visit_array_literal(self, node: 'ArrayLiteralNode') -> DSLValue:
        pass

    @abstractmethod
    def visit_object_literal(self, node: 'ObjectLiteralNode') -> DSLValue:
        pass

    @abstractmethod
    def visit_pipe(self, node: 'PipeNode') -> DSLValue:
        pass


# AST Node implementations
class LiteralNode(ASTNode):
    """Literal value node."""

    def __init__(self, value: Any):
        self.value = value

    def accept(self, visitor: ASTVisitor) -> DSLValue:
        return visitor.visit_literal(self)


class IdentifierNode(ASTNode):
    """Identifier node."""

    def __init__(self, name: str):
        self.name = name

    def accept(self, visitor: ASTVisitor) -> DSLValue:
        return visitor.visit_identifier(self)


class MemberAccessNode(ASTNode):
    """Member access node (obj.prop or obj[key])."""

    def __init__(
        self, object: ASTNode, property: str | ASTNode, computed: bool = False
    ):
        self.object = object
        self.property = property
        self.computed = computed  # True for obj[key], False for obj.prop

    def accept(self, visitor: ASTVisitor) -> DSLValue:
        return visitor.visit_member_access(self)


class FunctionCallNode(ASTNode):
    """Function call node."""

    def __init__(self, function: ASTNode, arguments: list[ASTNode]):
        self.function = function
        self.arguments = arguments

    def accept(self, visitor: ASTVisitor) -> DSLValue:
        return visitor.visit_function_call(self)


class BinaryOperationNode(ASTNode):
    """Binary operation node."""

    def __init__(self, left: ASTNode, operator: str, right: ASTNode):
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: ASTVisitor) -> DSLValue:
        return visitor.visit_binary_operation(self)


class UnaryOperationNode(ASTNode):
    """Unary operation node."""

    def __init__(self, operator: str, operand: ASTNode):
        self.operator = operator
        self.operand = operand

    def accept(self, visitor: ASTVisitor) -> DSLValue:
        return visitor.visit_unary_operation(self)


class ConditionalNode(ASTNode):
    """Conditional (ternary) operation node."""

    def __init__(
        self, condition: ASTNode, true_expr: ASTNode, false_expr: ASTNode
    ):
        self.condition = condition
        self.true_expr = true_expr
        self.false_expr = false_expr

    def accept(self, visitor: ASTVisitor) -> DSLValue:
        return visitor.visit_conditional(self)


class ArrayLiteralNode(ASTNode):
    """Array literal node."""

    def __init__(self, elements: list[ASTNode]):
        self.elements = elements

    def accept(self, visitor: ASTVisitor) -> DSLValue:
        return visitor.visit_array_literal(self)


class ObjectLiteralNode(ASTNode):
    """Object literal node."""

    def __init__(self, properties: list[tuple[str, ASTNode]]):
        self.properties = properties

    def accept(self, visitor: ASTVisitor) -> DSLValue:
        return visitor.visit_object_literal(self)


class PipeNode(ASTNode):
    """Pipe operation node (data | function)."""

    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right

    def accept(self, visitor: ASTVisitor) -> DSLValue:
        return visitor.visit_pipe(self)
