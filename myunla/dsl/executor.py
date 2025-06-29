"""Executor for the API Template DSL."""

from typing import Optional

from myunla.dsl.context import DSLContext
from myunla.dsl.functions import get_function
from myunla.dsl.types import (
    ArrayLiteralNode,
    ASTNode,
    ASTVisitor,
    BinaryOperationNode,
    ConditionalNode,
    DSLError,
    DSLResult,
    DSLValue,
    DSLValueType,
    FunctionCallNode,
    IdentifierNode,
    LiteralNode,
    MemberAccessNode,
    ObjectLiteralNode,
    PipeNode,
    UnaryOperationNode,
)


class DSLExecutionError(Exception):
    """DSL execution error."""

    pass


class DSLExecutor(ASTVisitor):
    """Executor for DSL expressions using the visitor pattern."""

    def __init__(self):
        self.context: Optional[DSLContext] = None

    def execute(self, ast: ASTNode, context: DSLContext) -> DSLResult:
        """Execute AST with given context."""
        try:
            self.context = context
            result = ast.accept(self)
            return DSLResult(success=True, value=result.to_python())
        except Exception as e:
            return DSLResult(
                success=False, error=DSLError(str(e), "EXECUTION_ERROR")
            )

    def visit_literal(self, node: LiteralNode) -> DSLValue:
        """Visit literal node."""
        return DSLValue.from_python(node.value)

    def visit_identifier(self, node: IdentifierNode) -> DSLValue:
        """Visit identifier node."""
        # Check variables first
        var_value = self.context.get_variable(node.name)
        if var_value is not None:
            return var_value

        # Check data fields
        return self.context.get_data_field(node.name)

    def visit_member_access(self, node: MemberAccessNode) -> DSLValue:
        """Visit member access node."""
        obj = node.object.accept(self)

        if node.computed:
            # obj[key] access
            key = node.property.accept(self)
            return self._get_member(obj, key)
        else:
            # obj.prop access
            key = DSLValue.from_python(node.property)
            return self._get_member(obj, key)

    def _get_member(self, obj: DSLValue, key: DSLValue) -> DSLValue:
        """Get member from object."""
        if obj.type == DSLValueType.OBJECT:
            key_str = str(key.to_python())
            value = obj.value.get(key_str)
            return DSLValue.from_python(value)
        elif obj.type == DSLValueType.ARRAY:
            if key.type == DSLValueType.NUMBER:
                index = int(key.value)
                if 0 <= index < len(obj.value):
                    return DSLValue.from_python(obj.value[index])
            elif key.type == DSLValueType.STRING and key.value.isdigit():
                index = int(key.value)
                if 0 <= index < len(obj.value):
                    return DSLValue.from_python(obj.value[index])

        return DSLValue.from_python(None)

    def visit_function_call(self, node: FunctionCallNode) -> DSLValue:
        """Visit function call node."""
        func = node.function.accept(self)

        # Get function name
        if isinstance(node.function, IdentifierNode):
            func_name = node.function.name
        else:
            raise DSLExecutionError("Invalid function call")

        # Get built-in function
        builtin_func = get_function(func_name)
        if builtin_func:
            # Evaluate arguments
            args = [arg.accept(self) for arg in node.arguments]
            try:
                return builtin_func(*args)
            except Exception as e:
                raise DSLExecutionError(f"Function '{func_name}' error: {e!s}")

        # Check if it's a callable value
        if func.type == DSLValueType.FUNCTION:
            args = [arg.accept(self) for arg in node.arguments]
            try:
                return func.value(*args)
            except Exception as e:
                raise DSLExecutionError(f"Function call error: {e!s}")

        raise DSLExecutionError(f"Unknown function: {func_name}")

    def visit_binary_operation(self, node: BinaryOperationNode) -> DSLValue:
        """Visit binary operation node."""
        left = node.left.accept(self)
        right = node.right.accept(self)

        return self._apply_binary_operator(node.operator, left, right)

    def _apply_binary_operator(
        self, op: str, left: DSLValue, right: DSLValue
    ) -> DSLValue:
        """Apply binary operator."""
        # Arithmetic operators
        if op == '+':
            return self._add(left, right)
        elif op == '-':
            return self._subtract(left, right)
        elif op == '*':
            return self._multiply(left, right)
        elif op == '/':
            return self._divide(left, right)
        elif op == '%':
            return self._modulo(left, right)

        # Comparison operators
        elif op == '==':
            return DSLValue.from_python(self._equals(left, right))
        elif op == '!=':
            return DSLValue.from_python(not self._equals(left, right))
        elif op == '<':
            return DSLValue.from_python(self._less_than(left, right))
        elif op == '<=':
            return DSLValue.from_python(
                self._less_than(left, right) or self._equals(left, right)
            )
        elif op == '>':
            return DSLValue.from_python(self._greater_than(left, right))
        elif op == '>=':
            return DSLValue.from_python(
                self._greater_than(left, right) or self._equals(left, right)
            )

        # Logical operators
        elif op == '&&':
            return DSLValue.from_python(left.is_truthy() and right.is_truthy())
        elif op == '||':
            return DSLValue.from_python(left.is_truthy() or right.is_truthy())

        else:
            raise DSLExecutionError(f"Unknown operator: {op}")

    def _add(self, left: DSLValue, right: DSLValue) -> DSLValue:
        """Add operation."""
        if (
            left.type == DSLValueType.NUMBER
            and right.type == DSLValueType.NUMBER
        ):
            return DSLValue.from_python(left.value + right.value)
        elif (
            left.type == DSLValueType.STRING
            or right.type == DSLValueType.STRING
        ):
            return DSLValue.from_python(
                str(left.to_python()) + str(right.to_python())
            )
        elif (
            left.type == DSLValueType.ARRAY and right.type == DSLValueType.ARRAY
        ):
            return DSLValue.from_python(left.value + right.value)
        else:
            return DSLValue.from_python(left.to_python() + right.to_python())

    def _subtract(self, left: DSLValue, right: DSLValue) -> DSLValue:
        """Subtract operation."""
        if (
            left.type == DSLValueType.NUMBER
            and right.type == DSLValueType.NUMBER
        ):
            return DSLValue.from_python(left.value - right.value)
        else:
            raise DSLExecutionError("Cannot subtract non-numbers")

    def _multiply(self, left: DSLValue, right: DSLValue) -> DSLValue:
        """Multiply operation."""
        if (
            left.type == DSLValueType.NUMBER
            and right.type == DSLValueType.NUMBER
        ):
            return DSLValue.from_python(left.value * right.value)
        elif (
            left.type == DSLValueType.STRING
            and right.type == DSLValueType.NUMBER
        ):
            return DSLValue.from_python(left.value * int(right.value))
        elif (
            left.type == DSLValueType.ARRAY
            and right.type == DSLValueType.NUMBER
        ):
            return DSLValue.from_python(left.value * int(right.value))
        else:
            raise DSLExecutionError("Invalid operands for multiplication")

    def _divide(self, left: DSLValue, right: DSLValue) -> DSLValue:
        """Divide operation."""
        if (
            left.type == DSLValueType.NUMBER
            and right.type == DSLValueType.NUMBER
        ):
            if right.value == 0:
                raise DSLExecutionError("Division by zero")
            return DSLValue.from_python(left.value / right.value)
        else:
            raise DSLExecutionError("Cannot divide non-numbers")

    def _modulo(self, left: DSLValue, right: DSLValue) -> DSLValue:
        """Modulo operation."""
        if (
            left.type == DSLValueType.NUMBER
            and right.type == DSLValueType.NUMBER
        ):
            if right.value == 0:
                raise DSLExecutionError("Modulo by zero")
            return DSLValue.from_python(left.value % right.value)
        else:
            raise DSLExecutionError("Cannot modulo non-numbers")

    def _equals(self, left: DSLValue, right: DSLValue) -> bool:
        """Equality comparison."""
        return left.to_python() == right.to_python()

    def _less_than(self, left: DSLValue, right: DSLValue) -> bool:
        """Less than comparison."""
        try:
            return left.to_python() < right.to_python()
        except TypeError:
            return False

    def _greater_than(self, left: DSLValue, right: DSLValue) -> bool:
        """Greater than comparison."""
        try:
            return left.to_python() > right.to_python()
        except TypeError:
            return False

    def visit_unary_operation(self, node: UnaryOperationNode) -> DSLValue:
        """Visit unary operation node."""
        operand = node.operand.accept(self)

        if node.operator == '!':
            return DSLValue.from_python(not operand.is_truthy())
        elif node.operator == '-':
            if operand.type == DSLValueType.NUMBER:
                return DSLValue.from_python(-operand.value)
            else:
                raise DSLExecutionError("Cannot negate non-number")
        else:
            raise DSLExecutionError(f"Unknown unary operator: {node.operator}")

    def visit_conditional(self, node: ConditionalNode) -> DSLValue:
        """Visit conditional (ternary) node."""
        condition = node.condition.accept(self)

        if condition.is_truthy():
            return node.true_expr.accept(self)
        else:
            return node.false_expr.accept(self)

    def visit_array_literal(self, node: ArrayLiteralNode) -> DSLValue:
        """Visit array literal node."""
        elements = [elem.accept(self).to_python() for elem in node.elements]
        return DSLValue.from_python(elements)

    def visit_object_literal(self, node: ObjectLiteralNode) -> DSLValue:
        """Visit object literal node."""
        obj = {}
        for key, value_node in node.properties:
            value = value_node.accept(self)
            obj[key] = value.to_python()

        return DSLValue.from_python(obj)

    def visit_pipe(self, node: PipeNode) -> DSLValue:
        """Visit pipe operation node."""
        left_value = node.left.accept(self)

        # If right side is a function call, inject the piped value as first argument
        if isinstance(node.right, FunctionCallNode):
            return self._execute_pipe_function_call(left_value, node.right)
        
        # Fallback: Create a temporary context with the piped value as 'data'
        pipe_context = self.context.create_child_context(
            {'data': left_value.to_python()}
        )
        old_context = self.context

        try:
            self.context = pipe_context
            return node.right.accept(self)
        finally:
            self.context = old_context

    def _execute_pipe_function_call(self, piped_value: DSLValue, func_call: FunctionCallNode) -> DSLValue:
        """Execute function call with piped value as first argument."""
        # Get function name
        if isinstance(func_call.function, IdentifierNode):
            func_name = func_call.function.name
        else:
            raise DSLExecutionError("Invalid function call in pipe")

        # Get built-in function
        builtin_func = get_function(func_name)
        if builtin_func:
            # Evaluate original arguments
            original_args = [arg.accept(self) for arg in func_call.arguments]
            # Inject piped value as first argument
            all_args = [piped_value] + original_args
            try:
                return builtin_func(*all_args)
            except Exception as e:
                raise DSLExecutionError(f"Function '{func_name}' error: {e!s}")

        raise DSLExecutionError(f"Unknown function: {func_name}")
