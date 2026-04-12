from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.response import ok
from backend.db.session import get_db
from backend.services.history_service import HistoryService


router = APIRouter(prefix="/history", tags=["history"])


@router.get("/me")
async def my_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    payload = await HistoryService(db).get_my_history(user_id=user.id, page=page, size=size)
    return ok(payload.model_dump())


@router.get("/matches/{match_id}")
async def match_detail(
    match_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    payload = await HistoryService(db).get_match_detail(user_id=user.id, match_id=match_id)
    return ok(payload.model_dump())
