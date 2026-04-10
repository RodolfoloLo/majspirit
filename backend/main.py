from uuid import uuid4

from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware

from backend.api.health import router as health_router
from backend.api.auth import router as auth_router
from backend.api.rooms import router as rooms_router
from backend.api.ws import router as ws_router
from backend.api.history import router as history_router
from backend.api.games import router as games_router
from backend.core.config import settings
from backend.core.exceptions import register_exception_handlers
from backend.core.request_context import set_request_id


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version="0.1.0")

    @app.middleware("http")
    async def inject_request_id(request:Request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid4())
        set_request_id(request_id)
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins or [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
    )
    register_exception_handlers(app)

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(rooms_router, prefix="/api/v1")
    app.include_router(history_router, prefix="/api/v1")
    app.include_router(games_router, prefix="/api/v1")
    app.include_router(ws_router, prefix="/api/v1")
    return app


app = create_app()