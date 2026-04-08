from fastapi import APIRouter

from backend.core.response import ok

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return ok({"status": "ok"})