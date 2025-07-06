from http.client import NOT_FOUND

from fastapi import APIRouter, HTTPException, Request

from myunla.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
async def gateway_handler(
    request: Request,
    path: str,
):
    parts = path.split("/")
    if len(parts) < 3:
        raise HTTPException(NOT_FOUND)
    path_prefix = "/".join(parts[:-1])
    endpoint = parts[-1]
    print(path_prefix, endpoint)
