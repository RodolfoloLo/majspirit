from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.response import ok
from backend.db.session import get_db
from backend.schemas.game import DiscardReq
from backend.services.game_service import game_service
from backend.services.history_service import HistoryService
from backend.ws.events import GAME_DISCARDED
from backend.ws.manager import ws_manager


router = APIRouter(prefix="/games", tags=["games"])


async def _broadcast_game_events(event_data: dict) -> None:
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


async def _persist_if_match_end(game_id: int, db: AsyncSession) -> None:
    if not game_service.is_match_finished(game_id):
        return
    if game_service.is_persisted(game_id):
        return

    summary = game_service.build_match_result(game_id)
    await HistoryService(db).save_match_result(summary)
    game_service.mark_persisted(game_id)


@router.get("/{game_id}/state")
async def game_state(game_id: int, user=Depends(get_current_user)):
    payload = game_service.get_state(game_id=game_id, user_id=user.id)
    return ok(payload)


@router.get("/{game_id}/actions/available")
async def available_actions(game_id: int, user=Depends(get_current_user)):
    payload = game_service.get_available_actions(game_id=game_id, user_id=user.id)
    return ok(payload)


@router.post("/{game_id}/actions/discard")
async def discard(
    game_id: int,
    payload: DiscardReq,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    event_data = game_service.discard(game_id=game_id, user_id=user.id, tile=payload.tile)
    await _persist_if_match_end(game_id, db)
    await _broadcast_game_events(event_data)
    return ok(event_data)


@router.post("/{game_id}/actions/draw")
async def draw(game_id: int, user=Depends(get_current_user)):
    _ = game_id
    _ = user
    game_service.action_not_available()


@router.post("/{game_id}/actions/tsumo")
async def tsumo(game_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    event_data = game_service.tsumo(game_id=game_id, user_id=user.id)
    await _persist_if_match_end(game_id, db)
    await _broadcast_game_events(event_data)
    return ok(event_data)


@router.post("/{game_id}/actions/ron")
async def ron(game_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    event_data = game_service.ron(game_id=game_id, user_id=user.id)
    await _persist_if_match_end(game_id, db)
    await _broadcast_game_events(event_data)
    return ok(event_data)


@router.post("/{game_id}/actions/pass")
async def pass_action(game_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    event_data = game_service.pass_action(game_id=game_id, user_id=user.id)
    await _persist_if_match_end(game_id, db)
    await _broadcast_game_events(event_data)
    return ok(event_data)
