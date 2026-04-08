from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.room import Room
from backend.models.room_player import RoomPlayer


class RoomRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_room(self, name: str, owner_id: int, max_players: int = 4) -> Room:
        room = Room(name=name, owner_id=owner_id, max_players=max_players)
        self.db.add(room)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def get_room(self, room_id: int) -> Room | None:
        stmt = select(Room).where(Room.id == room_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_rooms(self, page: int, size: int, status: str | None = None) -> list[Room]:
        stmt = select(Room)
        if status:
            stmt = stmt.where(Room.status == status)
        stmt = stmt.order_by(Room.id.desc()).offset((page - 1) * size).limit(size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_player(self, room_id: int, user_id: int, seat: int) -> RoomPlayer:
        rp = RoomPlayer(room_id=room_id, user_id=user_id, seat=seat)
        self.db.add(rp)
        await self.db.commit()
        await self.db.refresh(rp)
        return rp

    async def list_players(self, room_id: int) -> list[RoomPlayer]:
        stmt = select(RoomPlayer).where(RoomPlayer.room_id == room_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_player(self, room_id: int, user_id: int) -> RoomPlayer | None:
        stmt = select(RoomPlayer).where(
            RoomPlayer.room_id == room_id,
            RoomPlayer.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_ready(self, room_player: RoomPlayer, ready: bool) -> None:
        room_player.ready = ready
        await self.db.commit()

    async def delete_player(self, room_id: int, user_id: int) -> None:
        stmt = select(RoomPlayer).where(
            RoomPlayer.room_id == room_id,
            RoomPlayer.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        rp = result.scalar_one_or_none()
        if rp:
            await self.db.delete(rp)
            await self.db.commit()