from fastapi import FastAPI

from backend.api.health import router as health_router
from backend.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version="0.1.0")
    app.include_router(health_router, prefix="/api/v1")
    return app


app = create_app()