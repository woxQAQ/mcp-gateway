import datetime
import json
import uuid
from typing import Any, Optional

import yaml
from openapi_core import OpenAPI

from api.mcp import Cors, HttpServer, Mcp, Router, Tool


class OpenAPIConverter:
    """
    OpenAPI规范到MCP配置转换器

    将OpenAPI 3.0规范文件转换为MCP（Model Context Protocol）配置，
    自动生成工具定义、路由配置和HTTP服务器配置。
    """

    def __init__(
        self,
        oas_path: Optional[str] = None,
        oas_content: Optional[bytes] = None,
    ):
        """
        初始化OpenAPI转换器

        Args:
            oas_path: OpenAPI规范文件路径（支持JSON和YAML格式）
            oas_content: OpenAPI规范文件内容（字节格式）

        Raises:
            ValueError: 当oas_path和oas_content都未提供时
            Exception: OpenAPI规范解析失败时
        """
        if oas_path:
            oas = self._load_from_file(oas_path)
        elif oas_content:
            oas = self._load_from_content(oas_content)
        else:
            raise ValueError("必须提供 oas_path 或 oas_content 参数")

        try:
            self.spec = OpenAPI.from_dict(oas).spec
        except Exception as e:
            print(e)
            raise e

    def _load_from_file(self, file_path: str) -> dict:
        """
        从文件加载OpenAPI规范

        Args:
            file_path: 文件路径，支持.json和.yaml/.yml文件

        Returns:
            dict: 解析后的OpenAPI规范字典
        """
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.endswith(".json"):
                return json.load(f)
            else:  # 默认按YAML处理
                return yaml.safe_load(f)

    def _load_from_content(self, content: bytes) -> dict:
        """
        从字节内容加载OpenAPI规范

        Args:
            content: OpenAPI规范的字节内容

        Returns:
            dict: 解析后的OpenAPI规范字典
        """
        text = content.decode("utf-8")
        try:
            # 尝试解析为JSON
            return json.loads(text)
        except json.JSONDecodeError:
            # JSON解析失败，尝试YAML
            return yaml.safe_load(text)

    def convert(self):
        """
        将OpenAPI规范转换为MCP配置

        创建包含HTTP服务器、路由器和工具定义的完整MCP配置。

        Returns:
            Mcp: 完整的MCP配置对象
        """
        rs = self._get_random_str()
        # 创建基础MCP配置
        mcp_config = Mcp(
            name=self.spec["info"]["title"].replace(" ", "_") + "_" + rs,
            tenant_name="default",
            updated_at=datetime.datetime.now(),
            created_at=datetime.datetime.now(),
            deleted_at=None,
            servers=[],
            routers=[],
            tools=[],
            http_servers=[],
        )

        # 创建HTTP服务器配置
        server_config = HttpServer(
            name=mcp_config.name,
            description=self.spec["info"]["description"],
            url=len(self.spec["servers"]) > 0
            and self.spec["servers"][0]["url"]
            or "",
            tools=[],
        )

        # 创建路由器配置，包含CORS设置
        router_config = Router(
            prefix=f"/mcp/{rs}",
            sse_prefix="",
            server=server_config.name,
            cors=Cors(
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allow_headers=[
                    "Authorization",
                    "Content-Type",
                    "mcp-protocol-version",
                    "Mcp-Session-Id",
                ],
                expose_headers=["Mcp-Session-Id", "mcp-protocol-version"],
            ),
        )

        # 解析并生成工具定义
        self._get_tools(mcp_config, server_config)
        mcp_config.http_servers.append(server_config)
        mcp_config.routers.append(router_config)
        return mcp_config

    def _get_random_str(self, length: int = 10) -> str:
        """
        生成随机名称

        Args:
            length: 随机名称长度，默认为10

        Returns:
            str: 基于UUID生成的随机字符串
        """
        return uuid.uuid4().hex[:length]

    def _get_tools(self, mcp_config: Mcp, server_config: HttpServer):
        """
        从OpenAPI规范中提取并生成工具定义

        遍历OpenAPI规范中的所有路径和操作，为每个操作创建对应的MCP工具。

        Args:
            mcp_config: MCP配置对象，工具将添加到此对象中
            server_config: HTTP服务器配置对象
        """
        for path, path_item in self.spec["paths"].items():
            for method, operation in path_item.items():
                if method == "options":
                    continue

                # 生成操作ID（如果不存在）
                if (
                    "operationId" not in operation
                    or operation["operationId"] == ""
                ):
                    pathparts = path.split("/")[1:]
                    operation["operationId"] = (
                        "_".join(pathparts) + "_" + method
                    )

                # 创建工具定义
                tool = Tool(
                    name=operation["operationId"],
                    description=operation["summary"]
                    or operation["description"],
                    method=method,
                    path="{{config.url}}" + path,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": "Bearer {{request.headers.Authorization}}",
                    },
                    args=[],
                    request_body="",
                    response_body="{{response.body}}",
                    input_schema={},
                )

                # 解析参数：查询参数、头部参数、路径参数
                query_params, header_params, path_params = self._get_params(
                    operation, tool
                )
                # 解析请求体参数
                body_params = self._get_request_body(
                    self.spec.get("components", {}), operation, tool
                )
                tool.args = (
                    query_params + header_params + path_params + body_params
                )

                # 构建请求体模板
                if len(body_params) > 0:
                    s = "{\n"
                    for i, _body in enumerate(body_params):
                        s += '     {name}: {{{{ args.{name} | tojson }}}}'.format(
                            name=_body["name"]
                        )
                        if i < len(body_params) - 1:
                            s += ",\n"
                    s += "\n}"
                    tool.request_body = s

                mcp_config.tools.append(tool)
                server_config.tools.append(tool.name)

    def _get_request_body(self, components, operation: Any, tool: Tool) -> Any:
        """
        解析OpenAPI操作的请求体参数

        从OpenAPI操作定义中提取请求体schema，并转换为MCP工具参数。

        Args:
            components: OpenAPI规范的components部分，包含共享的schema定义
            operation: OpenAPI操作对象
            tool: MCP工具对象，用于设置请求体内容类型

        Returns:
            list: 请求体参数列表
        """
        body = []
        if operation.get("requestBody"):
            body_required = operation["requestBody"]["required"]
            for content_type, media_type in operation["requestBody"][
                "content"
            ].items():
                if content_type != "application/json":
                    continue
                tool.request_body = content_type
                schema = media_type.get("schema")
                if not schema:
                    continue

                # 处理schema引用
                if "$ref" in schema:
                    refname = schema["$ref"].removeprefix(
                        "#/components/schemas/"
                    )
                    if (
                        refname
                        and "schemas" in components
                        and refname in components["schemas"]
                    ):
                        schema = components["schemas"][refname]

                # 解析schema属性
                props = schema.get("properties")
                if not props:
                    continue
                for name, prop in props.items():
                    # 跳过系统生成的字段
                    if (
                        name.endswith("response")
                        or name == "Id"
                        or name == "createdAt"
                    ):
                        continue
                    arg = {
                        "name": name,
                        "position": "body",
                        "type": 'string',
                        "required": body_required
                        or name in schema.get("required", []),
                        "description": prop.get("description", ""),
                    }

                    # 处理参数类型
                    _type = prop.get("type")
                    if _type:
                        if type(_type) is list and len(_type) > 1:
                            arg["type"] = _type[0]
                            if arg["type"] == "array" and 'items' in prop:
                                arg["items"] = prop["items"]
                        else:
                            arg["type"] = _type

                    # 设置默认值
                    default = prop.get("default")
                    if default:
                        arg["default"] = default
                    body.append(arg)
        return body

    def _get_params(self, operatons: Any, tool: Tool) -> Any:
        """
        解析OpenAPI操作的参数定义

        从OpenAPI操作中提取查询参数、头部参数和路径参数。

        Args:
            operatons: OpenAPI操作对象
            tool: MCP工具对象，用于设置路径模板和头部

        Returns:
            tuple: (查询参数列表, 头部参数列表, 路径参数列表)
        """
        query_params = []
        header_params = []
        path_params = []
        if "parameters" not in operatons:
            return query_params, header_params, path_params

        for param in operatons["parameters"]:
            arg = {
                "name": param["name"],
                "position": param["in"],
                "type": "string",
                "required": param.get("required", False),
                "description": param.get("description", ""),
            }

            if param.get("schema"):
                schema_type = param["schema"].get("type", "string")
                default = param["schema"].get("default")
                _in = param["in"]
                if default:
                    arg["default"] = default
                arg["type"] = schema_type

                # 根据参数位置分类处理
                if _in == "query":
                    query_params.append(arg)
                elif _in == "header":
                    header_params.append(arg)
                    # 为头部参数设置Jinja模板占位符
                    tool.headers[arg["name"]] = "{" + arg["name"] + "}"
                elif _in == "path":
                    arg["required"] = True
                    path_params.append(arg)
                    # 替换路径中的参数占位符
                    tool.path = tool.path.replace(
                        "{" + arg["name"] + "}",
                        "{{args." + arg["name"] + "}}",
                    )

        return query_params, header_params, path_params


if __name__ == "__main__":
    # 示例用法：转换petstore OpenAPI规范
    conv = OpenAPIConverter("oas/petstore.v3.yaml")
    cfg = conv.convert()

    # 默认字符串输出 (YAML)
    print("=== YAML FORMAT (Default) ===")
    print(cfg)  # 明确调用 str()
