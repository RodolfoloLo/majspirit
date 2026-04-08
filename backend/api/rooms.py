from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.response import ok
from backend.db.session import get_db
from backend.schemas.room import RoomCreateReq, RoomJoinReq, RoomReadyReq
from backend.services.room_service import RoomService


router = APIRouter(prefix="/rooms", tags=["rooms"])

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
async def get_room_detail(room_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    service = RoomService(db)
    room = await service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="room not found")

    players = await service.repo.list_players(room_id)
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
    try:
        rp = await service.join_room(room_id, user.id, payload.seat)
        return ok({"room_id": room_id, "user_id": rp.user_id, "seat": rp.seat})
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_409_CONFLICT if detail in {"room is full", "already in room", "seat occupied"} else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail)


@router.post("/{room_id}/ready")
async def ready_room(room_id: int, payload: RoomReadyReq, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    service = RoomService(db)
    try:
        await service.set_ready(room_id, user.id, payload.ready)
        return ok({"room_id": room_id, "ready": payload.ready})
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{room_id}/start")
async def start_room(room_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    service = RoomService(db)
    room = await service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="room not found")
    if room.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only owner can start")

    can_start = await service.can_start(room_id)
    if not can_start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="room cannot start")
    return ok({"room_id": room_id, "started": True})

@router.post("/{room_id}/leave")
async def leave_room(
    room_id: int, 
    db: AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
    ):
    service = RoomService(db)
    try:
        await service.leave_room(room_id, user.id)
        return ok({"room_id": room_id, "user_id": user.id, "left": True})
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if detail == "room not found" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail)