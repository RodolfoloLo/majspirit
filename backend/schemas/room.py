from datetime import datetime
from pydantic import BaseModel, Field,ConfigDict

class RoomCreateReq(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    max_players: int = Field(default=4, ge=4, le=4)

class RoomJoinReq(BaseModel):
    seat: int = Field(ge=0, le=3)

class RoomReadyReq(BaseModel):
    ready: bool


class RoomState(BaseModel):
    id: int
    name: str
    owner_id: int
    status: str
    max_players: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RoomListResp(BaseModel):
    items: list[RoomState]
    page: int
    size: int


class RoomPlayer(BaseModel):
    user_id: int
    seat: int
    ready: bool

    model_config = ConfigDict(from_attributes=True)

class RoomStateResp(BaseModel):
    room_id: int
    name: str
    owner_id: int
    status: str
    max_players: int
    players: list[RoomPlayer]

    model_config = ConfigDict(from_attributes=True)

class RoomBuiltResp(BaseModel):
    room_id: int
    status: str

class RoomJoinedResp(BaseModel):
    room_id: int
    user_id: int
    seat: int

class RoomReadyResp(BaseModel):
    room_id: int
    ready: bool

class RoomStartedResp(BaseModel):
    room_id: int
    started: bool

class RoomLeaveResp(BaseModel):
    room_id: int
    user_id: int
    left: bool

#怎么判断要不要给Pydantic模型添加ConfigDict(from_attributes=True)？如果你的Pydantic模型需要从一个ORM对象（如SQLAlchemy模型）创建实例，并且你希望Pydantic能够正确地从ORM对象的属性中提取数据，那么你应该添加ConfigDict(from_attributes=True)。这告诉Pydantic在创建模型实例时，可以直接从ORM对象的属性中获取值，而不是仅仅依赖于传入的字典数据。