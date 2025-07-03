from typing import Any

from pydantic import BaseModel


class RequestWrapper(BaseModel):
    headers: dict[str, str]
    query: dict[str, str]
    body: dict[str, Any]
    path: dict[str, str]
    cookies: dict[str, str]


class ResponseWrapper(BaseModel):
    data: dict[str, Any]
    body: dict[str, Any]


class Context(BaseModel):
    args: dict[str, Any]
    config: dict[str, str]
    request: RequestWrapper
    response: ResponseWrapper
