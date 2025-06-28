import datetime
import json
import random
import string
from typing import Any

import yaml
from openapi_core import OpenAPI

from api.mcp import Cors, HttpServer, Mcp, Router, Tool


class OpenAPIConverter:
    def __init__(self, oas_path: str):
        with open(oas_path, "r") as f:
            if f.name.endswith(".json"):
                oas = json.load(f)
            elif f.name.endswith(".yaml") or f.name.endswith(".yml"):
                oas = yaml.safe_load(f)
            try:
                self.spec = OpenAPI.from_dict(oas).spec
            except Exception as e:
                print(e)
                raise e

    def convert(self):
        random.seed(datetime.datetime.now().timestamp())
        mcp_config = Mcp(
            name=self.spec["info"]["title"] + self._get_random_name(),
            updated_at=datetime.datetime.now(),
            created_at=datetime.datetime.now(),
        )

        server_config = HttpServer(
            name=mcp_config.name,
            description=self.spec["info"]["description"],
            url=len(self.spec["servers"]) > 0
            and self.spec["servers"][0]["url"]
            or "",
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
        mcp_config.servers.append(server_config)
        mcp_config.routers.append(router_config)
        return mcp_config, server_config

    def _get_random_name(self, length: int = 10) -> str:
        return "".join(
            random.choices(string.ascii_letters + string.digits, k=length)
        )

    def _get_tools(self, mcp_config: Mcp, server_config: HttpServer):
        for path, path_item in self.spec["paths"].items():
            for method, operation in path_item.items():
                if method == "options":
                    continue
                if operation["operationId"] == "":
                    pathparts = path.split("/")[1:]
                    operation["operationId"] = (
                        pathparts[0].join("_") + "_" + method
                    )
                tool = Tool(
                    name=operation["operationId"],
                    description=operation["summary"]
                    or operation["description"],
                    method=method,
                    # TODO: jinja template system placeholder
                    path="{url}" + path,
                    headers={
                        "Content-Type": "application/json",
                        # TODO: jinja template system placeholder
                        "Authorization": "Bearer {token}",
                    },
                )
                query_params, header_params, path_params = (
                    self._get_path_params(operation, tool)
                )
                body_params = self._get_request_body(
                    self.spec["components"], operation, tool
                )
                tool.args = (
                    query_params + header_params + path_params + body_params
                )

                if len(body_params) > 0:
                    # TODO: jinja template system placeholder
                    pass
                mcp_config.tools.append(tool)
                server_config.tools.append(tool.name)

    def _get_request_body(self, components, operation: Any, tool: Tool) -> Any:
        body = []
        if operation["requestBody"]:
            body_required = operation["requestBody"]["required"]
            for content_type, media_type in operation["requestBody"][
                "content"
            ].items():
                if content_type != "application/json":
                    continue
                tool.request_body = content_type
                schema = media_type["schema"]
                if not schema:
                    continue
                refname = schema["ref"].removeprefix("#/components/schemas/")
                if refname and refname in components["schemas"]:
                    schema = components["schemas"][refname]
                props = schema["properties"]
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
                        "required": body_required or name in schema["required"],
                        "description": prop["description"],
                    }
                    _type = prop["type"]
                    if type(_type) is list and len(_type) > 1:
                        arg.type = _type[0]
                        if arg.type == "array" and 'items' in prop:
                            arg.items = prop["items"]
                    default = prop["default"]
                    if default:
                        arg["default"] = default
                    body.append(arg)
        return body

    def _get_path_params(self, operatons: Any, tool: Tool) -> Any:
        query_params = []
        header_params = []
        path_params = []
        for param in operatons["parameters"]:
            arg = {
                "name": param["name"],
                "position": param["in"],
                "type": "string",
                "required": param["required"],
                "description": param["description"],
            }
            if param["schema"]:
                type = param["schema"]["type"]
                default = param["schema"]["default"]
                _in = param["schema"]["in"]
                arg["default"] = default
                arg["type"] = type
                match _in:
                    case "query":
                        query_params.append(arg)
                    case "header":
                        header_params.append(arg)
                        # TODO: jinja template system placeholder
                        tool.headers[arg["name"]] = "{" + arg["name"] + "}"
                    case "path":
                        arg["required"] = True
                        path_params.append(arg)

        return query_params, header_params, path_params


if __name__ == "__main__":
    conv = OpenAPIConverter("oas/petstore.v3.yaml")
    print(conv.spec["paths"])
