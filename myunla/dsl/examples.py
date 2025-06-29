"""Examples demonstrating the API Template DSL usage."""

from . import parse_and_execute, validate_expression


def basic_examples():
    """Basic DSL usage examples."""

    # Example 1: Simple value access
    context = {
        "user": {"name": "Alice", "id": 123},
        "endpoint": "https://api.example.com",
    }

    # Access user name
    result = parse_and_execute("user.name", context)
    print(f"User name: {result.value}")  # "Alice"

    # Build URL with template
    result = parse_and_execute(
        'endpoint + "/users/" + toString(user.id)', context
    )
    print(f"URL: {result.value}")  # "https://api.example.com/users/123"


def api_template_examples():
    """API template examples."""

    # Example: OpenAPI parameter mapping
    context = {
        "args": {"userId": "u123", "format": "json"},
        "config": {"baseUrl": "https://api.example.com", "apiKey": "key123"},
        "request": {"headers": {"Authorization": "Bearer token"}},
    }

    # URL construction
    url_template = (
        'config.baseUrl + "/users/" + args.userId + "?format=" + args.format'
    )
    result = parse_and_execute(url_template, context)
    print(f"URL: {result.value}")

    # Headers construction
    headers_template = '''
    {
        "Authorization": request.headers.Authorization,
        "X-API-Key": config.apiKey,
        "Content-Type": "application/json"
    }
    '''
    result = parse_and_execute(headers_template, context)
    print(f"Headers: {result.value}")


def data_transformation_examples():
    """Data transformation examples."""

    context = {
        "users": [
            {"name": "Alice", "age": 30, "active": True},
            {"name": "Bob", "age": 25, "active": False},
            {"name": "Charlie", "age": 35, "active": True},
        ]
    }

    # Filter active users using new filterActive function
    filter_expr = 'users | filterActive()'
    result = parse_and_execute(filter_expr, context)
    print(f"Active users: {result.value}")

    # Transform to name list using pluck and join
    names_expr = 'users | getNames() | join(", ")'
    result = parse_and_execute(names_expr, context)
    print(f"Names: {result.value}")

    # Alternative: Filter by specific property and value
    filter_by_expr = 'users | filterBy("active", true)'
    result = parse_and_execute(filter_by_expr, context)
    print(f"Active users (filterBy): {result.value}")

    # Get only the names of active users
    active_names_expr = 'users | filterActive() | getNames() | join(", ")'
    result = parse_and_execute(active_names_expr, context)
    print(f"Active user names: {result.value}")


def conditional_examples():
    """Conditional logic examples."""

    context = {
        "user": {"role": "admin", "permissions": ["read", "write"]},
        "action": "delete",
    }

    # Conditional access control (更直观的语法)
    access_expr = '''
    user.role == "admin" ?
        "allowed" :
        ((user.permissions | includes(action)) ? "allowed" : "denied")
    '''
    result = parse_and_execute(access_expr, context)
    context["user"]["role"] = "user"
    result_user = parse_and_execute(access_expr, context)
    print(f"Access: {result.value}")
    print(f"Access: {result_user.value}")


def validation_examples():
    """Validation examples."""

    # Valid expressions
    expressions = [
        "user.name",
        "config.baseUrl + '/api'",
        "args.id ? toString(args.id) : 'default'",
        "[1, 2, 3] | length()",
        "{name: user.name, id: user.id}",
    ]

    for expr in expressions:
        result = validate_expression(expr)
        print(f"'{expr}' is {'valid' if result.success else 'invalid'}")


if __name__ == "__main__":
    print("=== Basic Examples ===")
    basic_examples()

    print("\n=== API Template Examples ===")
    api_template_examples()

    print("\n=== Data Transformation Examples ===")
    data_transformation_examples()

    print("\n=== Conditional Examples ===")
    conditional_examples()

    print("\n=== Validation Examples ===")
    validation_examples()
