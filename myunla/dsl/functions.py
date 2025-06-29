"""Built-in functions for the API Template DSL."""

import json
import re
from collections.abc import Callable
from typing import Optional

from myunla.dsl.types import DSLValue, DSLValueType

# Function registry
_functions: dict[str, Callable] = {}


def register_function(name: str, func: Callable):
    """Register a function in the DSL."""
    _functions[name] = func


def get_function(name: str) -> Optional[Callable]:
    """Get a function by name."""
    return _functions.get(name)


def get_all_functions() -> dict[str, Callable]:
    """Get all registered functions."""
    return _functions.copy()


# Built-in function implementations
def _toJSON(value: DSLValue) -> DSLValue:
    """Convert value to JSON string."""
    try:
        json_str = json.dumps(value.to_python(), ensure_ascii=False)
        return DSLValue.from_python(json_str)
    except (TypeError, ValueError) as e:
        return DSLValue.from_python(f"<JSON Error: {e!s}>")


def _fromJSON(value: DSLValue) -> DSLValue:
    """Parse JSON string to value."""
    if value.type != DSLValueType.STRING:
        return DSLValue.from_python(None)

    try:
        parsed = json.loads(value.value)
        return DSLValue.from_python(parsed)
    except (json.JSONDecodeError, TypeError):
        return DSLValue.from_python(None)


def _toString(value: DSLValue) -> DSLValue:
    """Convert value to string."""
    if value.type == DSLValueType.NULL:
        return DSLValue.from_python("")
    elif value.type == DSLValueType.STRING:
        return value
    elif value.type == DSLValueType.BOOLEAN:
        return DSLValue.from_python("true" if value.value else "false")
    elif value.type == DSLValueType.NUMBER:
        return DSLValue.from_python(str(value.value))
    elif value.type in (DSLValueType.ARRAY, DSLValueType.OBJECT):
        return DSLValue.from_python(json.dumps(value.value, ensure_ascii=False))
    else:
        return DSLValue.from_python(str(value.value))


def _toNumber(value: DSLValue) -> DSLValue:
    """Convert value to number."""
    if value.type == DSLValueType.NUMBER:
        return value
    elif value.type == DSLValueType.STRING:
        try:
            # Try integer first
            if value.value.isdigit() or (
                value.value.startswith('-') and value.value[1:].isdigit()
            ):
                return DSLValue.from_python(int(value.value))
            # Try float
            return DSLValue.from_python(float(value.value))
        except ValueError:
            return DSLValue.from_python(0)
    elif value.type == DSLValueType.BOOLEAN:
        return DSLValue.from_python(1 if value.value else 0)
    else:
        return DSLValue.from_python(0)


def _length(value: DSLValue) -> DSLValue:
    """Get length of array, object, or string."""
    if value.type in (DSLValueType.STRING, DSLValueType.ARRAY):
        return DSLValue.from_python(len(value.value))
    elif value.type == DSLValueType.OBJECT:
        return DSLValue.from_python(len(value.value))
    else:
        return DSLValue.from_python(0)


def _keys(value: DSLValue) -> DSLValue:
    """Get keys of an object."""
    if value.type == DSLValueType.OBJECT:
        return DSLValue.from_python(list(value.value.keys()))
    else:
        return DSLValue.from_python([])


def _values(value: DSLValue) -> DSLValue:
    """Get values of an object."""
    if value.type == DSLValueType.OBJECT:
        return DSLValue.from_python(list(value.value.values()))
    else:
        return DSLValue.from_python([])


def _map(array: DSLValue, func: DSLValue) -> DSLValue:
    """Map function over array."""
    if array.type != DSLValueType.ARRAY:
        return DSLValue.from_python([])

    if func.type != DSLValueType.FUNCTION:
        return array

    result = []
    for i, item in enumerate(array.value):
        item_value = DSLValue.from_python(item)
        index_value = DSLValue.from_python(i)
        mapped = func.value(item_value, index_value)
        result.append(mapped.to_python())

    return DSLValue.from_python(result)


def _filter(array: DSLValue, func: DSLValue) -> DSLValue:
    """Filter array using predicate function."""
    if array.type != DSLValueType.ARRAY:
        return DSLValue.from_python([])

    if func.type != DSLValueType.FUNCTION:
        return array

    result = []
    for i, item in enumerate(array.value):
        item_value = DSLValue.from_python(item)
        index_value = DSLValue.from_python(i)
        should_include = func.value(item_value, index_value)
        if should_include.is_truthy():
            result.append(item)

    return DSLValue.from_python(result)


def _find(array: DSLValue, func: DSLValue) -> DSLValue:
    """Find first element matching predicate."""
    if array.type != DSLValueType.ARRAY:
        return DSLValue.from_python(None)

    if func.type != DSLValueType.FUNCTION:
        return DSLValue.from_python(None)

    for i, item in enumerate(array.value):
        item_value = DSLValue.from_python(item)
        index_value = DSLValue.from_python(i)
        matches = func.value(item_value, index_value)
        if matches.is_truthy():
            return DSLValue.from_python(item)

    return DSLValue.from_python(None)


def _sort(array: DSLValue, key_func: Optional[DSLValue] = None) -> DSLValue:
    """Sort array."""
    if array.type != DSLValueType.ARRAY:
        return DSLValue.from_python([])

    try:
        if key_func and key_func.type == DSLValueType.FUNCTION:
            # Sort with key function
            def sort_key(item):
                item_value = DSLValue.from_python(item)
                key_result = key_func.value(item_value)
                return key_result.to_python()

            sorted_items = sorted(array.value, key=sort_key)
        else:
            # Sort naturally
            sorted_items = sorted(array.value)

        return DSLValue.from_python(sorted_items)
    except (TypeError, ValueError):
        # If sorting fails, return original array
        return array


def _slice(
    array: DSLValue, start: DSLValue, end: Optional[DSLValue] = None
) -> DSLValue:
    """Slice array."""
    if array.type not in (DSLValueType.ARRAY, DSLValueType.STRING):
        return DSLValue.from_python([])

    start_idx = start.to_python() if start.type == DSLValueType.NUMBER else 0
    end_idx = (
        end.to_python()
        if end and end.type == DSLValueType.NUMBER
        else len(array.value)
    )

    sliced = array.value[start_idx:end_idx]
    return DSLValue.from_python(sliced)


def _concat(*arrays: DSLValue) -> DSLValue:
    """Concatenate arrays."""
    result = []
    for array in arrays:
        if array.type == DSLValueType.ARRAY:
            result.extend(array.value)
        else:
            result.append(array.to_python())

    return DSLValue.from_python(result)


def _join(array: DSLValue, separator: DSLValue) -> DSLValue:
    """Join array elements into string."""
    if array.type != DSLValueType.ARRAY:
        return DSLValue.from_python("")

    sep = (
        separator.to_python() if separator.type == DSLValueType.STRING else ","
    )
    str_items = [str(item) for item in array.value]
    return DSLValue.from_python(sep.join(str_items))


def _split(string: DSLValue, separator: DSLValue) -> DSLValue:
    """Split string into array."""
    if string.type != DSLValueType.STRING:
        return DSLValue.from_python([])

    sep = (
        separator.to_python() if separator.type == DSLValueType.STRING else ","
    )
    parts = string.value.split(sep)
    return DSLValue.from_python(parts)


def _replace(
    string: DSLValue, search: DSLValue, replacement: DSLValue
) -> DSLValue:
    """Replace substring in string."""
    if string.type != DSLValueType.STRING:
        return string

    search_str = (
        search.to_python() if search.type == DSLValueType.STRING else ""
    )
    replace_str = (
        replacement.to_python()
        if replacement.type == DSLValueType.STRING
        else ""
    )

    result = string.value.replace(search_str, replace_str)
    return DSLValue.from_python(result)


def _match(string: DSLValue, pattern: DSLValue) -> DSLValue:
    """Test if string matches regex pattern."""
    if (
        string.type != DSLValueType.STRING
        or pattern.type != DSLValueType.STRING
    ):
        return DSLValue.from_python(False)

    try:
        return DSLValue.from_python(
            bool(re.search(pattern.value, string.value))
        )
    except re.error:
        return DSLValue.from_python(False)


def _extract(string: DSLValue, pattern: DSLValue) -> DSLValue:
    """Extract matches from string using regex."""
    if (
        string.type != DSLValueType.STRING
        or pattern.type != DSLValueType.STRING
    ):
        return DSLValue.from_python([])

    try:
        matches = re.findall(pattern.value, string.value)
        return DSLValue.from_python(matches)
    except re.error:
        return DSLValue.from_python([])


def _default(value: DSLValue, default_value: DSLValue) -> DSLValue:
    """Return default value if value is null or empty."""
    if value.type == DSLValueType.NULL:
        return default_value
    elif value.type == DSLValueType.STRING and len(value.value) == 0:
        return default_value
    elif value.type == DSLValueType.ARRAY and len(value.value) == 0:
        return default_value
    elif value.type == DSLValueType.OBJECT and len(value.value) == 0:
        return default_value
    else:
        return value


def _merge(*objects: DSLValue) -> DSLValue:
    """Merge objects."""
    result = {}
    for obj in objects:
        if obj.type == DSLValueType.OBJECT:
            result.update(obj.value)

    return DSLValue.from_python(result)


def _pick(obj: DSLValue, *keys: DSLValue) -> DSLValue:
    """Pick specific keys from object."""
    if obj.type != DSLValueType.OBJECT:
        return DSLValue.from_python({})

    result = {}
    for key in keys:
        if key.type == DSLValueType.STRING and key.value in obj.value:
            result[key.value] = obj.value[key.value]

    return DSLValue.from_python(result)


def _omit(obj: DSLValue, *keys: DSLValue) -> DSLValue:
    """Omit specific keys from object."""
    if obj.type != DSLValueType.OBJECT:
        return DSLValue.from_python({})

    result = obj.value.copy()
    for key in keys:
        if key.type == DSLValueType.STRING and key.value in result:
            del result[key.value]

    return DSLValue.from_python(result)


# Simplified filter and map functions for common use cases
def _filterBy(
    array: DSLValue, property_name: DSLValue, value: DSLValue = None
) -> DSLValue:
    """Filter array by property value."""
    if array.type != DSLValueType.ARRAY:
        return DSLValue.from_python([])

    if property_name.type != DSLValueType.STRING:
        return array

    prop_name = property_name.value
    result = []

    for item in array.value:
        if isinstance(item, dict) and prop_name in item:
            if value is None:
                # Filter by truthy value
                if item[prop_name]:
                    result.append(item)
            else:
                # Filter by exact value
                if item[prop_name] == value.to_python():
                    result.append(item)

    return DSLValue.from_python(result)


def _pluck(array: DSLValue, property_name: DSLValue) -> DSLValue:
    """Extract property values from array of objects."""
    if array.type != DSLValueType.ARRAY:
        return DSLValue.from_python([])

    if property_name.type != DSLValueType.STRING:
        return DSLValue.from_python([])

    prop_name = property_name.value
    result = []

    for item in array.value:
        if isinstance(item, dict) and prop_name in item:
            result.append(item[prop_name])

    return DSLValue.from_python(result)


def _filterActive(array: DSLValue) -> DSLValue:
    """Filter array for active items (active=true)."""
    return _filterBy(array, DSLValue.from_python("active"))


def _getNames(array: DSLValue) -> DSLValue:
    """Get names from array of objects."""
    return _pluck(array, DSLValue.from_python("name"))


def _includes(array: DSLValue, value: DSLValue) -> DSLValue:
    """Check if array includes a value."""
    if array.type != DSLValueType.ARRAY:
        return DSLValue.from_python(False)

    search_value = value.to_python()
    return DSLValue.from_python(search_value in array.value)


# Register all built-in functions
register_function("toJSON", _toJSON)
register_function("fromJSON", _fromJSON)
register_function("toString", _toString)
register_function("toNumber", _toNumber)
register_function("length", _length)
register_function("keys", _keys)
register_function("values", _values)
register_function("map", _map)
register_function("filter", _filter)
register_function("find", _find)
register_function("sort", _sort)
register_function("slice", _slice)
register_function("concat", _concat)
register_function("join", _join)
register_function("split", _split)
register_function("replace", _replace)
register_function("match", _match)
register_function("extract", _extract)
register_function("default", _default)
register_function("merge", _merge)
register_function("pick", _pick)
register_function("omit", _omit)
register_function("filterBy", _filterBy)
register_function("pluck", _pluck)
register_function("filterActive", _filterActive)
register_function("getNames", _getNames)
register_function("includes", _includes)
