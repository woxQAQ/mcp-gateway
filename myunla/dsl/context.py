"""Execution context for the API Template DSL."""

from typing import Any, Optional

from myunla.dsl.types import DSLValue


class DSLContext:
    """Execution context for DSL expressions."""

    def __init__(self, data: Optional[dict[str, Any]] = None):
        self.data = data or {}
        self.variables: dict[str, DSLValue] = {}
        self.parent: Optional[DSLContext] = None

    def set_variable(self, name: str, value: DSLValue):
        """Set a variable in the context."""
        self.variables[name] = value

    def get_variable(self, name: str) -> Optional[DSLValue]:
        """Get a variable from the context."""
        if name in self.variables:
            return self.variables[name]

        if self.parent:
            return self.parent.get_variable(name)

        return None

    def has_variable(self, name: str) -> bool:
        """Check if a variable exists in the context."""
        return self.get_variable(name) is not None

    def get_data_field(self, path: str) -> DSLValue:
        """Get a field from the data using dot notation."""
        parts = path.split('.')
        current = self.data

        try:
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list) and part.isdigit():
                    index = int(part)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        current = None
                else:
                    current = None
                    break

            return DSLValue.from_python(current)

        except (KeyError, IndexError, ValueError):
            return DSLValue.from_python(None)

    def create_child_context(
        self, additional_data: Optional[dict[str, Any]] = None
    ) -> 'DSLContext':
        """Create a child context."""
        child_data = self.data.copy()
        if additional_data:
            child_data.update(additional_data)

        child = DSLContext(child_data)
        child.parent = self
        return child

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for debugging."""
        return {
            'data': self.data,
            'variables': {k: v.to_python() for k, v in self.variables.items()},
            'has_parent': self.parent is not None,
        }


class ScopedContext:
    """Context manager for scoped variables."""

    def __init__(self, context: DSLContext, variables: dict[str, DSLValue]):
        self.context = context
        self.variables = variables
        self.old_variables: dict[str, Optional[DSLValue]] = {}

    def __enter__(self) -> DSLContext:
        # Save old variable values
        for name in self.variables:
            self.old_variables[name] = self.context.get_variable(name)
            self.context.set_variable(name, self.variables[name])

        return self.context

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old variable values
        for name, old_value in self.old_variables.items():
            if old_value is not None:
                self.context.set_variable(name, old_value)
            elif name in self.context.variables:
                del self.context.variables[name]
