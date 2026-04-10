from datetime import datetime

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
