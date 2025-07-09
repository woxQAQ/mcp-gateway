"""Utils package - 工具函数和类集合."""

# Auth相关
from .auth import (
    COOKIE_MAX_AGE,
    UserManager,
    cookie_authentication,
    current_user,
    fastapi_users,
    get_jwt_strategy,
    get_user_db,
    get_user_manager,
)

# Bootstrap相关
from .bootstrap import (
    check_and_create_default_data,
    create_default_admin,
    create_default_tenant,
    initialize_default_data,
)

# 日志相关
from .logger import get_logger

# MCP相关
from .mcp import check_mcp_tenant_permission

# Redis工具
from .redis_utils import split_by_multiple_delimiters

# 通用工具
__all__ = [
    # Auth
    "COOKIE_MAX_AGE",
    "UserManager",
    "current_user",
    "get_jwt_strategy",
    "get_user_manager",
    "get_user_db",
    "fastapi_users",
    "cookie_authentication",
    # Bootstrap
    "check_and_create_default_data",
    "create_default_admin",
    "create_default_tenant",
    "initialize_default_data",
    # Logger
    "get_logger",
    # MCP
    "check_mcp_tenant_permission",
    # Redis
    "split_by_multiple_delimiters",
]
