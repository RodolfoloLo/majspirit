from typing import Any
from fastapi.responses import JSONResponse

from backend.core.request_context import get_request_id


def ok(data: Any = None, message: str = "ok") -> JSONResponse:
    payload: dict[str, Any] = {
        "code": 0,
        "message": message,
        "data": data,
    }
    request_id = get_request_id()
    if request_id:
        payload["request_id"] = request_id
    return JSONResponse(content=payload)


def fail(code: int, message: str, data: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "code": code,
        "message": message,
        "data": data,
    }
    request_id = get_request_id()
    if request_id:
        payload["request_id"] = request_id
    return payload
