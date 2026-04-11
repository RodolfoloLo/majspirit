from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.response import ok
from backend.db.session import get_db
from backend.schemas.room import RoomCreateReq, RoomJoinReq, RoomReadyReq, RoomState, RoomListResp, RoomPlayer, RoomStateResp, RoomBuiltResp, RoomJoinedResp, RoomReadyResp,RoomStartedResp,RoomLeaveResp
from backend.services.room_service import RoomService


router = APIRouter(prefix="/rooms", tags=["rooms"])

#查看房间列表
@router.get("")
async def list_rooms(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = RoomService(db)
    rooms = await service.list_rooms(page=page, size=size, status=status_filter)
    table = RoomListResp(
        items=[RoomState.model_validate(r) for r in rooms],
        page=page,
        size=size,
    )
    return ok(table.model_dump())

#查看房间详情
@router.get("/{room_id}")
async def get_room_detail(
    room_id: int, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
):
    service = RoomService(db)
    room, players = await service.get_room_with_players(room_id)
    detail = RoomStateResp(
        room_id=room.id,
        name=room.name,
        owner_id=room.owner_id,
        status=room.status,
        max_players=room.max_players,
        players=[RoomPlayer.model_validate(p) for p in players],
    )
    return ok(detail.model_dump())

#创建房间
@router.post("")
async def create_room(
    payload: RoomCreateReq, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
):
    service = RoomService(db)
    room = await service.create_room(payload.name, user.id, payload.max_players)
    built = RoomBuiltResp(room_id=room.id, status=room.status)
    return ok(built.model_dump())


@router.post("/{room_id}/join")
async def join_room(
    room_id: int, 
    payload: RoomJoinReq, #选座位
    db: AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
):
    service = RoomService(db)
    rp = await service.join_room(room_id, user.id, payload.seat)
    joined = RoomJoinedResp(room_id=rp.room_id, user_id=rp.user_id, seat=rp.seat)
    return ok(joined.model_dump())


@router.post("/{room_id}/ready")
async def ready_room(
    room_id: int, 
    payload: RoomReadyReq, #true or false
    db: AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
):
    service = RoomService(db)
    await service.set_ready(room_id, user.id, payload.ready)
    ready = RoomReadyResp(room_id=room_id, ready=payload.ready)
    return ok(ready.model_dump())


@router.post("/{room_id}/start")
async def start_room(
    room_id: int, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
    ):
    service = RoomService(db)
    game_meta = await service.start_room(room_id, user.id)
    return ok({"room_id": room_id, "started": True, **game_meta})#**game_meta包含了游戏ID和玩家列表等信息，可以根据需要返回给前端。

@router.post("/{room_id}/leave")
async def leave_room(
    room_id: int, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
    ):
    service = RoomService(db)
    await service.leave_room(room_id, user.id)
    left = RoomLeaveResp(room_id=room_id, user_id=user.id, left=True)
    return ok(left.model_dump())