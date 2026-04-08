from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.room_repo import RoomRepo


class RoomService:
    def __init__(self, db: AsyncSession):
        self.repo = RoomRepo(db)

    async def create_room(self, name: str, owner_id: int, max_players: int = 4):
        room = await self.repo.create_room(name, owner_id, max_players)
        await self.repo.add_player(room.id, owner_id, seat=0)
        return room

    async def list_rooms(self, page: int, size: int, status: str | None = None):
        return await self.repo.list_rooms(page=page, size=size, status=status)

    async def join_room(self, room_id: int, user_id: int, seat: int):
        room = await self.repo.get_room(room_id)
        if not room:
            raise ValueError("room not found")
        players = await self.repo.list_players(room_id)
        if len(players) >= room.max_players:
            raise ValueError("room is full")
        for p in players:
            if p.user_id == user_id:
                raise ValueError("already in room")
            if p.seat == seat:
                raise ValueError("seat occupied")

        return await self.repo.add_player(room_id, user_id, seat)

    async def set_ready(self, room_id: int, user_id: int, ready: bool):
        rp = await self.repo.get_player(room_id, user_id)
        if not rp:
            raise ValueError("player not in room")
        await self.repo.update_ready(rp, ready)

    async def can_start(self, room_id: int) -> bool:
        room = await self.repo.get_room(room_id)
        if not room:
            return False
        players = await self.repo.list_players(room_id)
        if len(players) != room.max_players:
            return False
        return all(p.ready for p in players)

    async def get_room(self, room_id: int):
        return await self.repo.get_room(room_id)
    
    async def leave_room(self, room_id: int, user_id: int):
        room = await self.repo.get_room(room_id)
        if not room:
            raise ValueError("room not found")
        rp = await self.repo.get_player(room_id, user_id)
        if not rp:
            raise ValueError("player not in room")
        await self.repo.delete_player(room_id, user_id)