from enum import Enum

from fastapi import Request


class Language(str, Enum):
    """支持的语言枚举"""

    ZH_CN = "zh-CN"
    EN_US = "en-US"


class I18nMessages:
    """国际化消息定义"""

    _messages: dict[str, dict[str, str]] = {
        # 通用消息
        "success": {
            Language.ZH_CN: "操作成功",
            Language.EN_US: "Operation successful",
        },
        "failed": {
            Language.ZH_CN: "操作失败",
            Language.EN_US: "Operation failed",
        },
        "not_found": {
            Language.ZH_CN: "资源不存在",
            Language.EN_US: "Resource not found",
        },
        "unauthorized": {
            Language.ZH_CN: "未授权访问",
            Language.EN_US: "Unauthorized",
        },
        "forbidden": {Language.ZH_CN: "禁止访问", Language.EN_US: "Forbidden"},
        "invalid_request": {
            Language.ZH_CN: "请求参数无效",
            Language.EN_US: "Invalid request parameters",
        },
        "server_error": {
            Language.ZH_CN: "服务器内部错误",
            Language.EN_US: "Internal server error",
        },
        "create_failed": {
            Language.ZH_CN: "创建失败",
            Language.EN_US: "Creation failed",
        },
        "update_failed": {
            Language.ZH_CN: "更新失败",
            Language.EN_US: "Update failed",
        },
        "delete_failed": {
            Language.ZH_CN: "删除失败",
            Language.EN_US: "Delete failed",
        },
        "get_failed": {
            Language.ZH_CN: "获取失败",
            Language.EN_US: "Fetch failed",
        },
        "status_update_failed": {
            Language.ZH_CN: "状态更新失败",
            Language.EN_US: "Status update failed",
        },
        # 认证相关
        "auth.login_success": {
            Language.ZH_CN: "登录成功",
            Language.EN_US: "Login successful",
        },
        "auth.login_failed": {
            Language.ZH_CN: "登录失败",
            Language.EN_US: "Login failed",
        },
        "auth.invalid_credentials": {
            Language.ZH_CN: "用户名或密码错误",
            Language.EN_US: "Invalid credentials",
        },
        "auth.register_success": {
            Language.ZH_CN: "注册成功",
            Language.EN_US: "Registration successful",
        },
        "auth.register_failed": {
            Language.ZH_CN: "注册失败",
            Language.EN_US: "Registration failed",
        },
        "auth.username_exists": {
            Language.ZH_CN: "用户名已存在",
            Language.EN_US: "Username already exists",
        },
        "auth.email_exists": {
            Language.ZH_CN: "邮箱已存在",
            Language.EN_US: "Email already exists",
        },
        "auth.password_mismatch": {
            Language.ZH_CN: "密码确认不匹配",
            Language.EN_US: "Password confirmation does not match",
        },
        "auth.logout_success": {
            Language.ZH_CN: "登出成功",
            Language.EN_US: "Logout successful",
        },
        "auth.password_changed": {
            Language.ZH_CN: "密码修改成功",
            Language.EN_US: "Password changed successfully",
        },
        "auth.password_change_failed": {
            Language.ZH_CN: "密码修改失败",
            Language.EN_US: "Password change failed",
        },
        "auth.user_deleted": {
            Language.ZH_CN: "用户删除成功",
            Language.EN_US: "User deleted successfully",
        },
        "auth.user_updated": {
            Language.ZH_CN: "用户更新成功",
            Language.EN_US: "User updated successfully",
        },
        "auth.permission_denied": {
            Language.ZH_CN: "只能修改自己的密码",
            Language.EN_US: "You can only change your own password",
        },
        "auth.user_not_found": {
            Language.ZH_CN: "用户不存在",
            Language.EN_US: "User not found",
        },
        "auth.last_admin_error": {
            Language.ZH_CN: "不能删除最后一个管理员",
            Language.EN_US: "Cannot delete the last admin",
        },
        "auth.cannot_delete_self": {
            Language.ZH_CN: "不能删除自己",
            Language.EN_US: "Cannot delete yourself",
        },
        "auth.cannot_modify_self": {
            Language.ZH_CN: "不能修改自己的状态",
            Language.EN_US: "Cannot modify your own status",
        },
        "auth.cannot_disable_last_admin": {
            Language.ZH_CN: "不能禁用最后一个管理员",
            Language.EN_US: "Cannot disable the last admin",
        },
        # 租户相关
        "tenant.created": {
            Language.ZH_CN: "租户创建成功",
            Language.EN_US: "Tenant created successfully",
        },
        "tenant.updated": {
            Language.ZH_CN: "租户更新成功",
            Language.EN_US: "Tenant updated successfully",
        },
        "tenant.deleted": {
            Language.ZH_CN: "租户删除成功",
            Language.EN_US: "Tenant deleted successfully",
        },
        "tenant.name_exists": {
            Language.ZH_CN: "租户名称已存在",
            Language.EN_US: "Tenant name already exists",
        },
        "tenant.prefix_exists": {
            Language.ZH_CN: "租户前缀已存在",
            Language.EN_US: "Tenant prefix already exists",
        },
        "tenant.not_found": {
            Language.ZH_CN: "租户不存在",
            Language.EN_US: "Tenant not found",
        },
        "tenant.enabled": {
            Language.ZH_CN: "租户启用成功",
            Language.EN_US: "Tenant enabled successfully",
        },
        "tenant.disabled": {
            Language.ZH_CN: "租户禁用成功",
            Language.EN_US: "Tenant disabled successfully",
        },
        # MCP 配置相关
        "mcp.config_created": {
            Language.ZH_CN: "MCP配置创建成功",
            Language.EN_US: "MCP config created successfully",
        },
        "mcp.config_updated": {
            Language.ZH_CN: "MCP配置更新成功",
            Language.EN_US: "MCP config updated successfully",
        },
        "mcp.config_deleted": {
            Language.ZH_CN: "MCP配置删除成功",
            Language.EN_US: "MCP config deleted successfully",
        },
        "mcp.config_activated": {
            Language.ZH_CN: "MCP配置激活成功",
            Language.EN_US: "MCP config activated successfully",
        },
        "mcp.config_exists": {
            Language.ZH_CN: "配置名称已存在",
            Language.EN_US: "MCP config with this name already exists",
        },
        "mcp.config_not_found": {
            Language.ZH_CN: "MCP配置不存在",
            Language.EN_US: "MCP config not found",
        },
        "mcp.config_name_immutable": {
            Language.ZH_CN: "配置名称不能修改",
            Language.EN_US: "MCP config name cannot be changed",
        },
        "mcp.sync_success": {
            Language.ZH_CN: "配置同步成功",
            Language.EN_US: "Config synced successfully",
        },
    }

    @classmethod
    def get(cls, key: str, lang: Language = Language.ZH_CN) -> str:
        """获取国际化消息"""
        if key not in cls._messages:
            return key

        messages = cls._messages[key]
        return messages.get(lang, messages.get(Language.ZH_CN, key))


class I18nHelper:
    """国际化助手类"""

    @staticmethod
    def get_language_from_request(request: Request) -> Language:
        """从请求中获取语言偏好"""
        # 优先从查询参数获取
        lang_param = request.query_params.get("lang")
        if lang_param:
            try:
                return Language(lang_param)
            except ValueError:
                pass

        # 从 Accept-Language 头获取
        accept_language = request.headers.get("Accept-Language", "")
        if "zh" in accept_language.lower():
            return Language.ZH_CN
        elif "en" in accept_language.lower():
            return Language.EN_US

        # 默认返回中文
        return Language.ZH_CN

    @staticmethod
    def get_message(key: str, request: Request, **kwargs) -> str:
        """根据请求获取国际化消息"""
        lang = I18nHelper.get_language_from_request(request)
        message = I18nMessages.get(key, lang)

        # 支持消息模板变量替换
        if kwargs:
            try:
                message = message.format(**kwargs)
            except (KeyError, ValueError):
                pass

        return message


def get_i18n_message(key: str, request: Request, **kwargs) -> str:
    """获取国际化消息的便捷函数"""
    return I18nHelper.get_message(key, request, **kwargs)
