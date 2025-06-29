"""API Template DSL - A specialized DSL for API configuration and templating."""

from myunla.dsl.context import DSLContext
from myunla.dsl.executor import DSLExecutor
from myunla.dsl.functions import get_function, register_function
from myunla.dsl.parser import DSLParser
from myunla.dsl.types import DSLError, DSLResult, DSLValue

__version__ = "1.0.0"
__all__ = [
    "DSLParser",
    "DSLExecutor",
    "DSLContext",
    "DSLValue",
    "DSLError",
    "DSLResult",
    "register_function",
    "get_function",
    "parse_and_execute",
    "validate_expression",
]


def parse_and_execute(expression: str, context: dict) -> DSLResult:
    """Parse and execute a DSL expression with given context."""
    parser = DSLParser()
    executor = DSLExecutor()

    try:
        ast = parser.parse(expression)
        dsl_context = DSLContext(context)
        return executor.execute(ast, dsl_context)
    except Exception as e:
        return DSLResult(
            success=False, error=DSLError(str(e), "EXECUTION_ERROR")
        )


def validate_expression(expression: str) -> DSLResult:
    """Validate a DSL expression without executing it."""
    parser = DSLParser()
    try:
        parser.parse(expression)
        return DSLResult(success=True, value=True)
    except Exception as e:
        return DSLResult(success=False, error=DSLError(str(e), "PARSE_ERROR"))
