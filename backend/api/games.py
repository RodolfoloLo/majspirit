import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.response import ok
from backend.db.session import SessionLocal, get_db
from backend.exceptions.business import TooManyRequests
from backend.schemas.game import DiscardReq, GameActionsResp, GameStateResp
from backend.services.cache_service import CacheService
from backend.services.game_service import game_service
from backend.services.history_service import HistoryService
from backend.utils.rate_limit import check_rate_limit
from backend.utils.redis_client import redis_client
from backend.ws.events import GAME_DISCARDED, GAME_MATCH_END
from backend.ws.manager import ws_manager


router = APIRouter(prefix="/games", tags=["games"])
AUTO_STEP_DELAY_SECONDS = 2
GAME_CACHE_TTL_SECONDS = 3600 * 6 #游戏状态在缓存中的过期时间.
_auto_tasks: dict[int, asyncio.Task[None]] = {}
cache_service = CacheService()

#生成游戏状态缓存的键,格式为"game:state:{game_id}".
def game_cache_key(game_id: int) -> str:
    return f"game:state:{game_id}"

#从缓存中加载游戏状态到内存中,如果游戏已经在内存中了就不加载了.
async def load_game_from_cache(game_id: int) -> None:
    if game_service.has_game(game_id):
        #如果游戏已经在内存中了就不加载了,直接返回.
        return
    try:
        payload = await cache_service.get_json(game_cache_key(game_id))
        #如果缓存中有游戏状态就导入到内存中.
        if payload:
            game_service.import_game_state(payload)
    except Exception:
        pass

#将内存中的游戏状态保存到缓存中,如果游戏不在内存中了就不保存了.
async def save_game_to_cache(game_id: int) -> None:
    if not game_service.has_game(game_id):
        #如果游戏不在内存中了就不保存了,直接返回.
        return
    try:
        #将内存中的游戏状态导出为一个Python对象,然后保存到缓存中.
        payload = game_service.export_game_state(game_id)
        await cache_service.set_json(game_cache_key(game_id), payload, ttl_seconds=GAME_CACHE_TTL_SECONDS)
    except Exception:
        pass

#游戏操作锁,确保同一时间只有一个协程在操作同一个游戏,避免并发导致的数据不一致问题.首先尝试使用Redis分布式锁,如果Redis不可用则退化为内存锁.
@asynccontextmanager
async def game_operation_lock(game_id: int):
    lock = None
    acquired = False
    try:
        lock = redis_client.lock(f"lock:game:{game_id}", timeout=8, blocking_timeout=3)
        acquired = bool(await lock.acquire(blocking=True, blocking_timeout=3))
    except Exception:
        lock = None
        acquired = False

    if lock and acquired:
        try:
            yield
        finally:
            try:
                await lock.release()
            except Exception:
                pass
        return

    async with game_service.lock_for(game_id):
        yield

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
    await save_game_to_cache(game_id)


async def run_auto_progress(game_id: int) -> None:
    try:
        while True:
            await asyncio.sleep(AUTO_STEP_DELAY_SECONDS)
            async with game_operation_lock(game_id):
                await load_game_from_cache(game_id)
                if not game_service.has_game(game_id):
                    return
                event_data = game_service.auto_progress(game_id)
                if event_data:
                    await save_game_to_cache(game_id)

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
    await load_game_from_cache(game_id)
    state = game_service.get_state(game_id=game_id, user_id=user.id)
    payload = GameStateResp.model_validate(state).model_dump()
    return ok(payload)

@router.get("/{game_id}/actions/available")
async def available_actions(game_id: int, user=Depends(get_current_user)):
    await load_game_from_cache(game_id)
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
    if not await check_rate_limit(f"game:discard:{user.id}:{game_id}", window_seconds=30):
        raise TooManyRequests()

    async with game_operation_lock(game_id):
        await load_game_from_cache(game_id)
        event_data = game_service.discard(game_id=game_id, user_id=user.id, tile=payload.tile)
        await save_game_to_cache(game_id)
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
    if not await check_rate_limit(f"game:tsumo:{user.id}:{game_id}", window_seconds=30):
        raise TooManyRequests()

    async with game_operation_lock(game_id):
        await load_game_from_cache(game_id)
        event_data = game_service.tsumo(game_id=game_id, user_id=user.id)
        await save_game_to_cache(game_id)
    await persist_if_match_end(game_id, db)
    await broadcast_game_events(event_data)
    schedule_auto_progress(game_id)
    return ok(event_data)

@router.post("/{game_id}/actions/ron")
async def ron(game_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if not await check_rate_limit(f"game:ron:{user.id}:{game_id}", window_seconds=30):
        raise TooManyRequests()

    async with game_operation_lock(game_id):
        await load_game_from_cache(game_id)
        event_data = game_service.ron(game_id=game_id, user_id=user.id)
        await save_game_to_cache(game_id)
    await persist_if_match_end(game_id, db)
    await broadcast_game_events(event_data)
    schedule_auto_progress(game_id)
    return ok(event_data)

@router.post("/{game_id}/actions/peng")
async def peng(game_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if not await check_rate_limit(f"game:peng:{user.id}:{game_id}", window_seconds=30):
        raise TooManyRequests()

    async with game_operation_lock(game_id):
        await load_game_from_cache(game_id)
        event_data = game_service.peng(game_id=game_id, user_id=user.id)
        await save_game_to_cache(game_id)
    await persist_if_match_end(game_id, db)
    await broadcast_game_events(event_data)
    schedule_auto_progress(game_id)
    return ok(event_data)
