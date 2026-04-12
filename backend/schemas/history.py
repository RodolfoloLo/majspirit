from datetime import datetime
from typing import Any

from pydantic import BaseModel


class HistoryItemResp(BaseModel):
    match_id: int
    finished_at: datetime | None = None
    rank: int
    final_score: int
    score_delta: int


class HistoryListResp(BaseModel):
    items: list[HistoryItemResp]
    page: int
    size: int
    total: int | None = None


class MatchDetailResp(BaseModel):
    match_id: int
    room_id: int
    created_at: datetime | None = None
    detail: dict[str, Any]
