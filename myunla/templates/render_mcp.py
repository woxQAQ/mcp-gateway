import json
from typing import Any, Optional
from urllib.parse import urljoin

from jinja2 import Environment

from api.mcp import HttpServer, Mcp, Tool
from myunla.templates.context import Context, RequestWrapper, ResponseWrapper
from myunla.utils.logger import get_logger

logger = get_logger(__name__)


class McpRequestMapper:
    """MCP请求到RESTful API请求的映射器"""

    def __init__(self, mcp_config: Mcp):
        """
        初始化映射器

        Args:
            mcp_config: MCP配置信息
        """
        self.mcp_config = mcp_config
        self.jinja_env = Environment()

    def find_tool_by_name(self, tool_name: str) -> Optional[Tool]:
        """
        根据工具名称查找工具配置

        Args:
            tool_name: 工具名称

        Returns:
            找到的工具配置，如果未找到则返回None
        """
        for tool in self.mcp_config.tools:
            if tool.name == tool_name:
                return tool
        return None

    def find_http_server_by_name(
        self, server_name: str
    ) -> Optional[HttpServer]:
        """
        根据服务器名称查找HTTP服务器配置

        Args:
            server_name: 服务器名称

        Returns:
            找到的HTTP服务器配置，如果未找到则返回None
        """
        for server in self.mcp_config.http_servers:
            if server.name == server_name:
                return server
        return None

    def find_http_server_for_tool(self, tool: Tool) -> Optional[HttpServer]:
        """
        为指定工具查找对应的HTTP服务器

        Args:
            tool: 工具配置

        Returns:
            对应的HTTP服务器配置，如果未找到则返回None
        """
        for server in self.mcp_config.http_servers:
            if tool.name in server.tools:
                return server
        return None

    def render_template(self, template_str: str, context: Context) -> str:
        """
        使用Jinja2渲染模板

        Args:
            template_str: 模板字符串
            context: 渲染上下文

        Returns:
            渲染后的字符串
        """
        try:
            template = self.jinja_env.from_string(template_str)
            return template.render(context.model_dump())
        except Exception as e:
            logger.error(f"模板渲染失败: {e}")
            raise ValueError(f"模板渲染失败: {e}")

    def build_request_context(
        self,
        tool_args: dict[str, Any],
        tool: Tool,
        request_headers: Optional[dict[str, str]] = None,
        request_cookies: Optional[dict[str, str]] = None,
    ) -> Context:
        """
        构建模板渲染所需的上下文

        Args:
            tool_args: 工具参数
            tool: 工具配置
            request_headers: 原始请求头
            request_cookies: 原始请求cookies

        Returns:
            渲染上下文
        """
        return Context(
            args=tool_args,
            config={
                "tool_name": tool.name,
                "method": tool.method,
                "path": tool.path,
                "description": tool.description,
            },
            request=RequestWrapper(
                headers=request_headers or {},
                query={},
                body=tool_args,
                path={},
                cookies=request_cookies or {},
            ),
            response=ResponseWrapper(data={}, body={}),
        )

    def map_mcp_to_restful(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        request_headers: Optional[dict[str, str]] = None,
        request_cookies: Optional[dict[str, str]] = None,
    ) -> tuple[str, str, dict[str, str], Optional[dict[str, Any]]]:
        """
        将MCP请求映射为RESTful API请求

        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            request_headers: 原始请求头
            request_cookies: 原始请求cookies

        Returns:
            Tuple包含: (method, url, headers, request_body)

        Raises:
            ValueError: 当工具未找到或配置错误时
        """
        # 1. 查找工具配置
        tool = self.find_tool_by_name(tool_name)
        if not tool:
            raise ValueError(f"工具 '{tool_name}' 未找到")

        # 2. 查找对应的HTTP服务器
        http_server = self.find_http_server_for_tool(tool)
        if not http_server:
            raise ValueError(f"工具 '{tool_name}' 没有对应的HTTP服务器配置")

        # 3. 构建渲染上下文
        context = self.build_request_context(
            tool_args, tool, request_headers, request_cookies
        )

        # 4. 渲染路径模板（支持路径参数）
        rendered_path = self.render_template(tool.path, context)

        # 5. 构建完整URL
        base_url = http_server.url.rstrip('/')
        full_url = urljoin(base_url + '/', rendered_path.lstrip('/'))

        # 6. 处理请求头
        headers = dict(tool.headers)  # 复制工具定义的头部
        if request_headers:
            # 合并原始请求头，工具定义的头部优先级更高
            for key, value in request_headers.items():
                if key.lower() not in [h.lower() for h in headers.keys()]:
                    headers[key] = value

        # 确保Content-Type设置正确
        if tool.method.upper() in [
            'POST',
            'PUT',
            'PATCH',
        ] and 'content-type' not in [h.lower() for h in headers.keys()]:
            headers['Content-Type'] = 'application/json'

        # 7. 渲染请求体模板
        request_body = None
        if tool.request_body and tool.method.upper() in [
            'POST',
            'PUT',
            'PATCH',
        ]:
            try:
                rendered_body = self.render_template(tool.request_body, context)
                # 尝试解析为JSON，验证格式正确性
                request_body = json.loads(rendered_body)
            except json.JSONDecodeError as e:
                logger.error(f"请求体JSON格式错误: {e}")
                raise ValueError(f"请求体JSON格式错误: {e}")

        logger.info(
            f"MCP工具 '{tool_name}' 映射为: {tool.method.upper()} {full_url}"
        )

        return tool.method.upper(), full_url, headers, request_body

    def validate_tool_args(
        self, tool_name: str, tool_args: dict[str, Any]
    ) -> bool:
        """
        验证工具参数是否符合输入模式

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            验证是否通过

        Raises:
            ValueError: 当工具未找到时
        """
        tool = self.find_tool_by_name(tool_name)
        if not tool:
            raise ValueError(f"工具 '{tool_name}' 未找到")

        # 如果工具定义了输入模式，进行验证
        if tool.input_schema:
            try:
                # 这里可以使用jsonschema库进行更严格的验证
                # 目前简化为检查必需字段是否存在
                required_fields = tool.input_schema.get('required', [])
                for field in required_fields:
                    if field not in tool_args:
                        logger.warning(
                            f"工具 '{tool_name}' 缺少必需参数: {field}"
                        )
                        return False

                logger.debug(f"工具 '{tool_name}' 参数验证通过")
                return True

            except Exception as e:
                logger.error(f"参数验证失败: {e}")
                return False

        # 如果没有定义输入模式，默认通过验证
        return True


def create_mcp_mapper(mcp_config: Mcp) -> McpRequestMapper:
    """
    创建MCP请求映射器的工厂函数

    Args:
        mcp_config: MCP配置

    Returns:
        MCP请求映射器实例
    """
    return McpRequestMapper(mcp_config)
