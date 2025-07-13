import json
from typing import Any, Optional

from fastapi import Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from mcp.types import JSONRPCRequest

from myunla.gateway.session import Connection, Message
from myunla.utils import get_logger

logger = get_logger(__name__)


async def send_accepted_response() -> Response:
    """发送接受响应"""
    return PlainTextResponse(
        content="Accepted", status_code=status.HTTP_202_ACCEPTED
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

    response_data = {
        "jsonrpc": "2.0",
        "id": jsonrpc_req.id,
        "result": result_data,
    }

    if send_via_sse and conn:
        # 通过SSE发送响应
        try:
            message = Message(
                event="message",
                data=json.dumps(response_data).encode('utf-8'),
            )
            await conn.send(message)
            return await send_accepted_response()
        except Exception as e:
            logger.error(f"通过SSE发送响应失败: {e}")
            return await send_protocol_error_with_id(
                "Failed to send response via SSE",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "InternalError",
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
        content=f'event: message\ndata: {json.dumps(response_data)}\n\n',
    )


async def send_protocol_error(
    message: str, status_code: int, error_code: str
) -> JSONResponse:
    """发送协议错误响应 (对应Go代码中的sendProtocolError)"""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": error_code, "message": message}},
    )


async def send_protocol_error_with_id(
    message: str,
    status_code: int,
    error_code: str,
    request_id: Optional[Any] = None,
) -> JSONResponse:
    """发送带请求ID的协议错误响应"""
    error_response = {
        "jsonrpc": "2.0",
        "error": {
            "code": error_code,
            "message": message,
        },
    }

    if request_id is not None:
        error_response["id"] = request_id

    return JSONResponse(
        status_code=status_code,
        content=error_response,
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
        "error": {
            "code": "ToolExecutionError",
            "message": f"Tool execution failed: {error!s}",
        },
    }

    if send_via_sse and conn:
        try:
            from myunla.gateway.session import Message

            message = Message(
                event="jsonrpc_error",
                data=json.dumps(error_response).encode('utf-8'),
            )
            await conn.send(message)
        except Exception as e:
            logger.error(f"通过SSE发送错误响应失败: {e}")

    return JSONResponse(
        content=error_response,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
