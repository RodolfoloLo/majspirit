import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.exceptions.business import BusinessError
from backend.core.response import fail


logger = logging.getLogger("uvicorn.error")


def _default_message(status_code: int) -> str:
    if status_code == status.HTTP_400_BAD_REQUEST:
        return "bad request"
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return "unauthorized"
    if status_code == status.HTTP_403_FORBIDDEN:
        return "forbidden"
    if status_code == status.HTTP_404_NOT_FOUND:
        return "not found"
    if status_code == status.HTTP_409_CONFLICT:
        return "conflict"
    if status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        return "method not allowed"
    if status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        return "unprocessable entity"
    if status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return "too many requests"
    return "internal server error"


def _status_to_business_code(status_code: int) -> int:
    mapping = {
        status.HTTP_400_BAD_REQUEST: 40001,
        status.HTTP_401_UNAUTHORIZED: 40101,
        status.HTTP_403_FORBIDDEN: 40301,
        status.HTTP_404_NOT_FOUND: 40401,
        status.HTTP_405_METHOD_NOT_ALLOWED: 40501,
        status.HTTP_409_CONFLICT: 40901,
        status.HTTP_422_UNPROCESSABLE_ENTITY: 42201,
        status.HTTP_429_TOO_MANY_REQUESTS: 42901,
    }
    return mapping.get(status_code, 50001)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessError)
    async def handle_business_error(_: Request, exc: BusinessError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=fail(code=exc.code, message=exc.message),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_starlette_http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else _default_message(exc.status_code)
        data = exc.detail if isinstance(exc.detail, (dict, list)) else None
        return JSONResponse(
            status_code=exc.status_code,
            content=fail(code=_status_to_business_code(exc.status_code), message=message, data=data),
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else _default_message(exc.status_code)
        data = exc.detail if isinstance(exc.detail, (dict, list)) else None
        return JSONResponse(
            status_code=exc.status_code,
            content=fail(code=_status_to_business_code(exc.status_code), message=message, data=data),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=fail(code=42201, message="validation error", data=exc.errors()),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception in API request", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=fail(code=50001, message="internal server error"),
        )