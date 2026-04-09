from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

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

                return await self.repo.add_player(room_id, user_id, seat)
        except IntegrityError as exc:
            message = str(exc.orig).lower() if getattr(exc, "orig", None) else str(exc).lower()
            if "uq_room_user" in message:
                raise AlreadyInRoom() from exc
            raise SeatOccupied() from exc

    async def set_ready(self, room_id: int, user_id: int, ready: bool):
        async with self.db.begin():
            rp = await self.repo.get_player(room_id, user_id)
            if not rp:
                raise PlayerNotInRoom()
            await self.repo.update_ready(rp, ready)

    async def start_room(self, room_id: int, user_id: int) -> bool:
        async with self.db.begin():
            room = await self.repo.get_room(room_id)
            if not room:
                raise RoomNotFound()
            if room.owner_id != user_id:
                raise OnlyOwnerCanStart()

            players = await self.repo.list_players(room_id)
            if len(players) != room.max_players or not all(p.ready for p in players):
                raise RoomCannotStart()

            room.status = "playing"
            return True

    async def leave_room(self, room_id: int, user_id: int):
        async with self.db.begin():
            room = await self.repo.get_room(room_id)
            if not room:
                raise RoomNotFound()

            rp = await self.repo.get_player(room_id, user_id)
            if not rp:
                raise PlayerNotInRoom()

            await self.repo.delete_player(rp)

#async with self.db.begin()的作用是开启一个数据库事务，确保在这个上下文中执行的所有数据库操作要么全部成功提交，要么在发生异常时全部回滚。这对于保持数据的一致性和完整性非常重要，尤其是在涉及多个相关数据库操作的情况下。