import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.response import ok
from backend.db.session import SessionLocal, get_db
from backend.schemas.game import DiscardReq, GameActionsResp, GameStateResp
from backend.services.game_service import game_service
from backend.services.history_service import HistoryService
from backend.ws.events import GAME_DISCARDED, GAME_MATCH_END
from backend.ws.manager import ws_manager


router = APIRouter(prefix="/games", tags=["games"])
AUTO_STEP_DELAY_SECONDS = 2
_auto_tasks: dict[int, asyncio.Task[None]] = {}

async def broadcast_game_events(event_data: dict[str, Any]) -> None:
    events = event_data.get("events") or [event_data]
    ts = datetime.now(timezone.utc).isoformat()
    for item in events:
        await ws_manager.broadcast(
            {
                "type": item.get("event_type", GAME_DISCARDED),
                "ts": ts,
                "data": item,
            }
        )

async def persist_if_match_end(game_id: int, db: AsyncSession) -> None:
    if not game_service.is_match_finished(game_id):
        return
    if game_service.is_persisted(game_id):
        return

    summary = game_service.build_match_result(game_id)
    await HistoryService(db).save_match_result(summary)
    game_service.mark_persisted(game_id)


async def run_auto_progress(game_id: int) -> None:
    try:
        while True:
            await asyncio.sleep(AUTO_STEP_DELAY_SECONDS)
            async with game_service.lock_for(game_id):
                event_data = game_service.auto_progress(game_id)

            if not event_data:
                return

            async with SessionLocal() as db:
                await persist_if_match_end(game_id, db)

            await broadcast_game_events(event_data)
            if event_data.get("event_type") == GAME_MATCH_END:
                return
    finally:
        _auto_tasks.pop(game_id, None)


def schedule_auto_progress(game_id: int) -> None:
    task = _auto_tasks.get(game_id)
    if task and not task.done():
        return
    _auto_tasks[game_id] = asyncio.create_task(run_auto_progress(game_id))

@router.get("/{game_id}/state")
async def game_state(game_id: int, user=Depends(get_current_user)):
    state = game_service.get_state(game_id=game_id, user_id=user.id)
    payload = GameStateResp.model_validate(state).model_dump()
    return ok(payload)

@router.get("/{game_id}/actions/available")
async def available_actions(game_id: int, user=Depends(get_current_user)):
    actions = game_service.get_available_actions(game_id=game_id, user_id=user.id)
    payload = GameActionsResp.model_validate(actions).model_dump()
    return ok(payload)

@router.post("/{game_id}/actions/discard")
async def discard(
    game_id: int,
    payload: DiscardReq,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    async with game_service.lock_for(game_id):
        event_data = game_service.discard(game_id=game_id, user_id=user.id, tile=payload.tile)
    await persist_if_match_end(game_id, db)
    await broadcast_game_events(event_data)
    schedule_auto_progress(game_id)
    return ok(event_data)

@router.post("/{game_id}/actions/draw")
async def draw(game_id: int, user=Depends(get_current_user)):
    _ = game_id
    _ = user
    game_service.action_not_available()

@router.post("/{game_id}/actions/tsumo")
async def tsumo(game_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    async with game_service.lock_for(game_id):
        event_data = game_service.tsumo(game_id=game_id, user_id=user.id)
    await persist_if_match_end(game_id, db)
    await broadcast_game_events(event_data)
    schedule_auto_progress(game_id)
    return ok(event_data)

@router.post("/{game_id}/actions/ron")
async def ron(game_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    async with game_service.lock_for(game_id):
        event_data = game_service.ron(game_id=game_id, user_id=user.id)
    await persist_if_match_end(game_id, db)
    await broadcast_game_events(event_data)
    schedule_auto_progress(game_id)
    return ok(event_data)

@router.post("/{game_id}/actions/peng")
async def peng(game_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    async with game_service.lock_for(game_id):
        event_data = game_service.peng(game_id=game_id, user_id=user.id)
    await persist_if_match_end(game_id, db)
    await broadcast_game_events(event_data)
    schedule_auto_progress(game_id)
    return ok(event_data)
