from datetime import datetime
from pydantic import BaseModel, Field,ConfigDict

class RoomCreateReq(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    max_players: int = Field(default=4, ge=2, le=4)

class RoomJoinReq(BaseModel):
    seat: int = Field(ge=0, le=3)

class RoomReadyReq(BaseModel):
    ready: bool

class RoomPlayerResp(BaseModel):
    user_id: int
    seat: int
    ready: bool

    model_config = ConfigDict(from_attributes=True)

class RoomResp(BaseModel):
    id: int
    name: str
    owner_id: int
    status: str
    max_players: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)