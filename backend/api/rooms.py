from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.response import ok
from backend.db.session import get_db
from backend.schemas.room import RoomCreateReq, RoomJoinReq, RoomReadyReq
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
    return ok({
        "items": [
            {
                "room_id": room.id,
                "name": room.name,
                "owner_id": room.owner_id,
                "status": room.status,
                "max_players": room.max_players,
                "created_at": room.created_at,
            }
            for room in rooms
        ],
        "page": page,
        "size": size,
    })

@router.get("/{room_id}")
async def get_room_detail(
    room_id: int, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
):
    service = RoomService(db)
    room, players = await service.get_room_with_players(room_id)
    return ok({
        "room_id": room.id,
        "name": room.name,
        "owner_id": room.owner_id,
        "status": room.status,
        "max_players": room.max_players,
        "players": [
            {
                "user_id": p.user_id,
                "seat": p.seat,
                "ready": p.ready,
            }
            for p in players
        ],
    })

@router.post("")
async def create_room(
    payload: RoomCreateReq, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
):
    service = RoomService(db)
    room = await service.create_room(payload.name, user.id, payload.max_players)
    return ok({"room_id": room.id, "status": room.status})


@router.post("/{room_id}/join")
async def join_room(
    room_id: int, 
    payload: RoomJoinReq, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
):
    service = RoomService(db)
    rp = await service.join_room(room_id, user.id, payload.seat)
    return ok({"room_id": room_id, "user_id": rp.user_id, "seat": rp.seat})


@router.post("/{room_id}/ready")
async def ready_room(
    room_id: int, 
    payload: RoomReadyReq, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
):
    service = RoomService(db)
    await service.set_ready(room_id, user.id, payload.ready)
    return ok({"room_id": room_id, "ready": payload.ready})


@router.post("/{room_id}/start")
async def start_room(
    room_id: int, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
    ):
    service = RoomService(db)
    game_meta = await service.start_room(room_id, user.id)
    return ok({"room_id": room_id, "started": True, **game_meta})

@router.post("/{room_id}/leave")
async def leave_room(
    room_id: int, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
    ):
    service = RoomService(db)
    await service.leave_room(room_id, user.id)
    return ok({"room_id": room_id, "user_id": user.id, "left": True})