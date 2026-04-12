from typing import Any

from pydantic import BaseModel, Field


class DiscardReq(BaseModel):
    tile: str = Field(min_length=2, max_length=10)

class GameStatePlayerResp(BaseModel):
    seat: int
    user_id: int
    is_bot: bool
    nickname: str
    hand_count: int
    discards: list[str]
    open_meld_count: int = 0
    open_melds: list[list[str]] = Field(default_factory=list)


class LastDiscardResp(BaseModel):
    seat: int
    tile: str
    next_turn_seat: int | None = None


class GameStateResp(BaseModel):
    game_id: int
    match_id: int
    round_index: int #当前第几轮了,从0开始.
    dealer_seat: int #本轮的庄家是哪个座位.
    turn_seat: int #现在轮到哪个座位操作了.
    wall_remaining: int
    status: str
    scores: list[int]
    players: list[GameStatePlayerResp]
    my_seat: int | None = None
    my_hand: list[str] | None = None
    pending_ron: list[int]
    pending_peng: list[int] = Field(default_factory=list)
    last_discard: LastDiscardResp | None = None


class GameActionsResp(BaseModel):
    seat: int | None = None
    actions: list[str]
    deadline_ms: int


class RuntimePlayerState(BaseModel):
    user_id: int
    seat: int
    hand: list[str] = Field(default_factory=list)
    discards: list[str] = Field(default_factory=list)
    open_meld_count: int = 0
    open_melds: list[list[str]] = Field(default_factory=list)
    is_bot: bool = False
    nickname: str


class RuntimeLastDiscard(BaseModel):
    seat: int
    tile: str
    next_turn_seat: int | None = None


class RuntimeRoundTurn(BaseModel):
    action: str
    seat: int
    tile: str | None = None
    from_seat: int | None = None
    at: str


class RuntimeRoundState(BaseModel):
    round_index: int
    dealer_seat: int
    initial_hands: dict[int, list[str]]
    initial_wall: list[str]
    turns: list[RuntimeRoundTurn] = Field(default_factory=list)
    result: dict[str, Any] | None = None


class RuntimeGameState(BaseModel):
    game_id: int
    match_id: int
    room_id: int
    round_index: int
    dealer_seat: int
    turn_seat: int
    wall: list[str] = Field(default_factory=list)
    status: str
    scores: list[int]
    initial_scores: list[int]
    players: dict[int, RuntimePlayerState]
    pending_ron: list[int] = Field(default_factory=list)
    pending_peng: list[int] = Field(default_factory=list)
    last_discard: RuntimeLastDiscard | None = None
    current_round: RuntimeRoundState | None = None
    round_logs: list[RuntimeRoundState] = Field(default_factory=list)
    persisted: bool = False
    final_ranking: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str