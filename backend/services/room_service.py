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
from backend.services.cache_service import CacheService
from backend.services.game_service import game_service
from backend.ws.events import ROOM_STARTED, ROOM_UPDATED
from backend.ws.manager import ws_manager

GAME_CACHE_TTL_SECONDS = 3600 * 6


def game_cache_key(game_id: int) -> str:
    return f"game:state:{game_id}"


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

    #注意些这种函数的时候一定要考虑多种情况.
    async def join_room(self, room_id: int, user_id: int, seat: int):
        try:
            async with self.db.begin():
                #第一步:检查房间是否存在.
                room = await self.repo.get_room(room_id)
                if not room:
                    raise RoomNotFound()
                
                #第二步:检查房间是否已经满员了.
                players = await self.repo.list_players(room_id)
                if len(players) >= room.max_players:
                    raise RoomIsFull()
                
                #第三步做两个检查:用户是否已经在房间里了,座位是否被占了.
                for p in players:
                    if p.user_id == user_id:
                        raise AlreadyInRoom()
                    if p.seat == seat:
                        raise SeatOccupied()

                #确认无误,才把你添加到房间
                joined = await self.repo.add_player(room_id, user_id, seat)
        #处理数据库完整性错误，判断是用户已经在房间里了还是座位被占了。
        except IntegrityError as exc:
            message = str(exc.orig).lower() if getattr(exc, "orig", None) else str(exc).lower()
            if "uq_room_user" in message:
                raise AlreadyInRoom() from exc
            raise SeatOccupied() from exc

        await self._broadcast_room_updated(room_id)
        return joined

    async def set_ready(self, room_id: int, user_id: int, ready: bool):
        async with self.db.begin():
            #第一步:检查你是否在这个房间.
            rp = await self.repo.get_player(room_id, user_id)
            if not rp:
                raise PlayerNotInRoom()
            #第二步:设置你的ready状态.(前端传来的)
            await self.repo.update_ready(rp, ready)
        await self._broadcast_room_updated(room_id)

    async def start_room(self, room_id: int, user_id: int) -> dict[str, int]:
        async with self.db.begin():
            room = await self.repo.get_room(room_id)
            #第一步:检查房间是否存在
            if not room:
                raise RoomNotFound()
            #第二步:检查你是不是房主
            if room.owner_id != user_id:
                raise OnlyOwnerCanStart()

            #检查房间是否有玩家以及玩家是否都ready.
            players = await self.repo.list_players(room_id)
            if not players or not all(p.ready for p in players):
                raise RoomCannotStart()

            #修改房间状态,创建游戏.
            room.status = "playing"
            game_meta = game_service.create_game(room_id=room_id, players=players)

        try:
            cache = CacheService()
            payload = game_service.export_game_state(game_meta["game_id"])
            await cache.set_json(game_cache_key(game_meta["game_id"]), payload, ttl_seconds=GAME_CACHE_TTL_SECONDS)
        except Exception:
            # Redis cache is best-effort and should not block start flow.
            pass

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
    #注意这个离开房间的函数不需要返回值，因为它的主要作用是修改数据库中的数据并广播房间状态更新，客户端可以通过监听房间状态更新事件来获取最新的房间信息。

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