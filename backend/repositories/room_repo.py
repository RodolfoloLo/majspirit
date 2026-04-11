from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.room import Room
from backend.models.room_player import RoomPlayer


class RoomRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_rooms(self, page: int, size: int, status: str | None = None) -> list[Room]:
        stmt = select(Room)
        if status:
            stmt = stmt.where(Room.status == status)
        stmt = stmt.order_by(Room.id.desc()).offset((page - 1) * size).limit(size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_room(self, room_id: int) -> Room | None:
        stmt = select(Room).where(Room.id == room_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_room(self, name: str, owner_id: int, max_players: int = 4) -> Room:
        room = Room(name=name, owner_id=owner_id, max_players=max_players)
        self.db.add(room)
        await self.db.flush()
        await self.db.refresh(room)
        #add+flush+refresh的组合可以确保在创建房间后，room对象的id等数据库生成的字段能够正确地被填充和返回。
        return room

    async def add_player(self, room_id: int, user_id: int, seat: int) -> RoomPlayer:
        rp = RoomPlayer(room_id=room_id, user_id=user_id, seat=seat)
        self.db.add(rp)
        await self.db.flush()
        await self.db.refresh(rp)
        return rp

    async def list_players(self, room_id: int) -> list[RoomPlayer]:
        stmt = select(RoomPlayer).where(RoomPlayer.room_id == room_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    #查找玩家在房间里的状态,主要是为了ready接口服务的.
    async def get_player(self, room_id: int, user_id: int) -> RoomPlayer | None:
        stmt = select(RoomPlayer).where(
            RoomPlayer.room_id == room_id,
            RoomPlayer.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_ready(self, room_player: RoomPlayer, ready: bool) -> None:
        room_player.ready = ready

    async def delete_player(self, room_player: RoomPlayer) -> None:
        await self.db.delete(room_player)

#flush()+refresh()组合作用是将新创建的对象持久化到数据库并刷新其状态以获取数据库生成的字段（如自增ID）。如果不调用flush()，对象不会被写入数据库，refresh()也无法获取到生成的ID等字段。