from sqlalchemy.ext.asyncio import AsyncSession

from backend.exceptions.business import MatchHistoryNotFound
from backend.repositories.history_repo import HistoryRepo
from backend.schemas.history import HistoryItemResp, HistoryListResp, MatchDetailResp


class HistoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = HistoryRepo(db)

    async def get_my_history(self, user_id: int, page: int, size: int) -> HistoryListResp:
        rows, total = await self.repo.list_by_user(user_id=user_id, page=page, size=size)
        items = [
            HistoryItemResp(
                match_id=row.match_id,
                finished_at=row.created_at,
                rank=row.rank,
                final_score=row.final_score,
                score_delta=row.score_delta,
            )
            for row in rows
        ]

        return HistoryListResp(
            items=items,
            page=page,
            size=size,
            total=total,
        )

    async def get_match_detail(self, user_id: int, match_id: int) -> MatchDetailResp:
        if not await self.repo.user_has_match(user_id=user_id, match_id=match_id):
            raise MatchHistoryNotFound()

        detail = await self.repo.get_match_detail(match_id)
        if not detail:
            raise MatchHistoryNotFound()

        return MatchDetailResp(
            match_id=detail.match_id,
            room_id=detail.room_id,
            created_at=detail.created_at,
            detail=detail.payload,
        )

    async def save_match_result(self, summary: dict) -> None:
        ranking = summary.get("ranking", [])
        if not ranking:
            return

        entries = [
            {
                "user_id": item["user_id"],
                "rank": item["rank"],
                "final_score": item["final_score"],
                "score_delta": item["score_delta"],
            }
            for item in ranking
            if int(item["user_id"]) > 0
        ]

        if not entries:
            return

        async with self.db.begin():
            await self.repo.save_match_result(
                match_id=summary["match_id"],
                room_id=summary["room_id"],
                entries=entries,
                detail_payload=summary,
            )
