from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from backend.exceptions.business import (
    AlreadyInRoom,
    OnlyOwnerCanStart,
    PlayerNotInRoom,
    RoomCannotStart,
    RoomIsFull,
    RoomNotFound,
    SeatOccupied,
)
from backend.repositories.room_repo import RoomRepo
from backend.services.game_service import game_service
from backend.ws.events import ROOM_STARTED, ROOM_UPDATED
from backend.ws.manager import ws_manager


class RoomService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RoomRepo(db)

    async def list_rooms(self, page: int, size: int, status: str | None = None):
        return await self.repo.list_rooms(page=page, size=size, status=status)

    async def get_room_with_players(self, room_id: int):
        room = await self.repo.get_room(room_id)
        if not room:
            raise RoomNotFound()
        players = await self.repo.list_players(room_id)
        return room, players

    async def create_room(self, name: str, owner_id: int, max_players: int = 4):
        async with self.db.begin():
            room = await self.repo.create_room(name, owner_id, max_players)
            await self.repo.add_player(room.id, owner_id, seat=0)
        await self._broadcast_room_updated(room.id)
        return room

    async def join_room(self, room_id: int, user_id: int, seat: int):
        try:
            async with self.db.begin():
                room = await self.repo.get_room(room_id)
                if not room:
                    raise RoomNotFound()

                players = await self.repo.list_players(room_id)
                if len(players) >= room.max_players:
                    raise RoomIsFull()

                for p in players:
                    if p.user_id == user_id:
                        raise AlreadyInRoom()
                    if p.seat == seat:
                        raise SeatOccupied()

                joined = await self.repo.add_player(room_id, user_id, seat)
        except IntegrityError as exc:
            message = str(exc.orig).lower() if getattr(exc, "orig", None) else str(exc).lower()
            if "uq_room_user" in message:
                raise AlreadyInRoom() from exc
            raise SeatOccupied() from exc

        await self._broadcast_room_updated(room_id)
        return joined

    async def set_ready(self, room_id: int, user_id: int, ready: bool):
        async with self.db.begin():
            rp = await self.repo.get_player(room_id, user_id)
            if not rp:
                raise PlayerNotInRoom()
            await self.repo.update_ready(rp, ready)
        await self._broadcast_room_updated(room_id)

    async def start_room(self, room_id: int, user_id: int) -> dict[str, int]:
        async with self.db.begin():
            room = await self.repo.get_room(room_id)
            if not room:
                raise RoomNotFound()
            if room.owner_id != user_id:
                raise OnlyOwnerCanStart()

            players = await self.repo.list_players(room_id)
            if not players or not all(p.ready for p in players):
                raise RoomCannotStart()

            room.status = "playing"
            game_meta = game_service.create_game(room_id=room_id, players=players)

        await ws_manager.broadcast(
            {
                "type": ROOM_STARTED,
                "ts": datetime.now(timezone.utc).isoformat(),
                "data": {"room_id": room_id, **game_meta},
            }
        )
        await self._broadcast_room_updated(room_id)
        return game_meta

    async def leave_room(self, room_id: int, user_id: int):
        async with self.db.begin():
            room = await self.repo.get_room(room_id)
            if not room:
                raise RoomNotFound()

            rp = await self.repo.get_player(room_id, user_id)
            if not rp:
                raise PlayerNotInRoom()

            await self.repo.delete_player(rp)
        await self._broadcast_room_updated(room_id)

    async def _broadcast_room_updated(self, room_id: int) -> None:
        room = await self.repo.get_room(room_id)
        if not room:
            return
        players = await self.repo.list_players(room_id)
        await ws_manager.broadcast(
            {
                "type": ROOM_UPDATED,
                "ts": datetime.now(timezone.utc).isoformat(),
                "data": {
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
                },
            }
        )

#async with self.db.begin()的作用是开启一个数据库事务，确保在这个上下文中执行的所有数据库操作要么全部成功提交，要么在发生异常时全部回滚。这对于保持数据的一致性和完整性非常重要，尤其是在涉及多个相关数据库操作的情况下。