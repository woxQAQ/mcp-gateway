import json
from typing import Any, Optional

from fastapi import Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from mcp import ErrorData, JSONRPCError, JSONRPCResponse
from mcp.types import (
    INTERNAL_ERROR,
    CallToolResult,
    JSONRPCRequest,
    TextContent,
)

from myunla.gateway.session import Connection, Message
from myunla.utils import get_logger

logger = get_logger(__name__)


async def send_accepted_response() -> Response:
    """发送接受响应"""
    return PlainTextResponse(
        content="Accepted", status_code=status.HTTP_202_ACCEPTED
    )


async def send_response(
    conn: Connection,
    jsonrpc_req: JSONRPCRequest,
    result: Any,
    send_via_sse: bool = False,
) -> Response:
    """发送响应"""
    if send_via_sse:
        try:
            message = Message(
                event="message",
                data=json.dumps(result).encode('utf-8'),
            )
            await conn.send(message)
            return await send_accepted_response()
        except Exception as e:
            logger.error(f"通过SSE发送响应失败: {e}")
            return send_protocol_error(
                "Failed to send response via SSE",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                INTERNAL_ERROR,
                jsonrpc_req.id,
            )
    return PlainTextResponse(
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Mcp-Session-Id": conn.meta().id,
        },
        status_code=status.HTTP_200_OK,
        content=f'event: message\ndata: {json.dumps(result)}\n\n',
    )


async def send_success_response(
    conn: Connection,
    jsonrpc_req: JSONRPCRequest,
    result: Any,
    send_via_sse: bool = False,
) -> Response:
    """发送成功响应"""
    # 处理结果序列化
    if hasattr(result, 'model_dump'):
        result_data = result.model_dump()
    elif hasattr(result, 'dict'):
        result_data = result.dict()
    else:
        result_data = result

    response_data = JSONRPCResponse(
        id=jsonrpc_req.id,
        jsonrpc="2.0",
        result=result_data,
    )
    return await send_response(conn, jsonrpc_req, response_data, send_via_sse)


def send_protocol_error(
    message: str,
    status_code: int,
    error_code: int,
    request_id: Optional[Any] = None,
) -> Response:
    """发送协议错误响应 (对应Go代码中的sendProtocolError)"""
    resp = JSONRPCError(
        id=request_id if request_id is not None else "",
        jsonrpc="2.0",
        error=ErrorData(
            code=error_code,
            message=message,
        ),
    )
    return JSONResponse(
        status_code=status_code,
        content=resp.model_dump(),
    )


async def send_tool_execution_error(
    conn,
    jsonrpc_req: JSONRPCRequest,
    error: Exception,
    send_via_sse: bool = False,
) -> Response:
    """发送工具执行错误响应"""
    error_response = {
        "jsonrpc": "2.0",
        "id": jsonrpc_req.id,
        "result": CallToolResult(
            isError=True,
            content=[
                TextContent(
                    text=f"Tool execution failed: {error!s}", type="text"
                )
            ],
        ),
    }
    return await send_response(conn, jsonrpc_req, error_response, send_via_sse)
