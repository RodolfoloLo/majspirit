from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from backend.exceptions.business import HistoryNotReady
from backend.models.match_detail import MatchDetail
from backend.models.match_history import MatchHistory


class HistoryRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_user(self, user_id: int, page: int, size: int) -> tuple[list[MatchHistory], int]:
        stmt = (
            select(MatchHistory)
            .where(MatchHistory.user_id == user_id)
            .order_by(MatchHistory.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        count_stmt = select(func.count()).select_from(MatchHistory).where(MatchHistory.user_id == user_id)
        try:
            rows_result = await self.db.execute(stmt)
            count_result = await self.db.execute(count_stmt)
        except SQLAlchemyError as exc:
            raise HistoryNotReady() from exc

        rows = list(rows_result.scalars().all())
        total = int(count_result.scalar_one())
        return rows, total

    async def user_has_match(self, user_id: int, match_id: int) -> bool:
        stmt = (
            select(func.count())
            .select_from(MatchHistory)
            .where(MatchHistory.user_id == user_id, MatchHistory.match_id == match_id)
        )
        try:
            result = await self.db.execute(stmt)
        except SQLAlchemyError as exc:
            raise HistoryNotReady() from exc
        return int(result.scalar_one()) > 0

    async def get_match_detail(self, match_id: int) -> MatchDetail | None:
        stmt = select(MatchDetail).where(MatchDetail.match_id == match_id)
        try:
            result = await self.db.execute(stmt)
        except SQLAlchemyError as exc:
            raise HistoryNotReady() from exc
        return result.scalar_one_or_none()

    async def save_match_result(
        self,
        match_id: int,
        room_id: int,
        entries: list[dict],
        detail_payload: dict,
    ) -> None:
        for entry in entries:
            self.db.add(
                MatchHistory(
                    match_id=match_id,
                    user_id=entry["user_id"],
                    rank=entry["rank"],
                    final_score=entry["final_score"],
                    score_delta=entry["score_delta"],
                )
            )

        existing = await self.get_match_detail(match_id)
        if existing:
            existing.payload = detail_payload
            existing.room_id = room_id
        else:
            self.db.add(
                MatchDetail(
                    match_id=match_id,
                    room_id=room_id,
                    payload=detail_payload,
                )
            )
