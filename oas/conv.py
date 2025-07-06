import datetime
import json
import uuid
from typing import Any, Optional

import yaml
from openapi_core import OpenAPI

from api.mcp import Cors, HttpServer, Mcp, Router, Tool


class OpenAPIConverter:
    def __init__(
        self,
        oas_path: Optional[str] = None,
        oas_content: Optional[bytes] = None,
    ):
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
        """从文件加载OpenAPI规范"""
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.endswith(".json"):
                return json.load(f)
            else:  # 默认按YAML处理
                return yaml.safe_load(f)

    def _load_from_content(self, content: bytes) -> dict:
        """从内容加载OpenAPI规范"""
        text = content.decode("utf-8")
        try:
            # 尝试解析为JSON
            return json.loads(text)
        except json.JSONDecodeError:
            # JSON解析失败，尝试YAML
            return yaml.safe_load(text)

    def convert(self):
        mcp_config = Mcp(
            name=self.spec["info"]["title"].replace(" ", "_")
            + "_"
            + self._get_random_name(),
            tenant_name="default",
            updated_at=datetime.datetime.now(),
            created_at=datetime.datetime.now(),
            deleted_at=None,
            servers=[],
            routers=[],
            tools=[],
            http_servers=[],
        )

        server_config = HttpServer(
            name=mcp_config.name,
            description=self.spec["info"]["description"],
            url=len(self.spec["servers"]) > 0
            and self.spec["servers"][0]["url"]
            or "",
            tools=[],
        )

        router_config = Router(
            prefix="/",
            http_server_ref=server_config,
            sse_prefix="/sse",
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
        self._get_tools(mcp_config, server_config)
        mcp_config.http_servers.append(server_config)
        mcp_config.routers.append(router_config)
        return mcp_config

    def _get_random_name(self, length: int = 10) -> str:
        """Generate a random name using UUID."""
        return uuid.uuid4().hex[:length]

    def _get_tools(self, mcp_config: Mcp, server_config: HttpServer):
        for path, path_item in self.spec["paths"].items():
            for method, operation in path_item.items():
                if method == "options":
                    continue
                if (
                    "operationId" not in operation
                    or operation["operationId"] == ""
                ):
                    pathparts = path.split("/")[1:]
                    operation["operationId"] = (
                        "_".join(pathparts) + "_" + method
                    )
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
                query_params, header_params, path_params = self._get_params(
                    operation, tool
                )
                body_params = self._get_request_body(
                    self.spec.get("components", {}), operation, tool
                )
                tool.args = (
                    query_params + header_params + path_params + body_params
                )

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
                props = schema.get("properties")
                if not props:
                    continue
                for name, prop in props.items():
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
                    _type = prop.get("type")
                    if _type:
                        if type(_type) is list and len(_type) > 1:
                            arg["type"] = _type[0]
                            if arg["type"] == "array" and 'items' in prop:
                                arg["items"] = prop["items"]
                        else:
                            arg["type"] = _type
                    default = prop.get("default")
                    if default:
                        arg["default"] = default
                    body.append(arg)
        return body

    def _get_params(self, operatons: Any, tool: Tool) -> Any:
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
                if _in == "query":
                    query_params.append(arg)
                elif _in == "header":
                    header_params.append(arg)
                    # TODO: jinja template system placeholder
                    tool.headers[arg["name"]] = "{" + arg["name"] + "}"
                elif _in == "path":
                    arg["required"] = True
                    path_params.append(arg)
                    tool.path = tool.path.replace(
                        "{" + arg["name"] + "}",
                        "{{args." + arg["name"] + "}}",
                    )

        return query_params, header_params, path_params


if __name__ == "__main__":
    conv = OpenAPIConverter("oas/petstore.v3.yaml")
    cfg = conv.convert()

    # 默认字符串输出 (YAML)
    print("=== YAML FORMAT (Default) ===")
    print(cfg)  # 明确调用 str()
