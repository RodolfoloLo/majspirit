from pydantic import BaseModel, Field


class DiscardReq(BaseModel):
    tile: str = Field(min_length=2, max_length=10)


class ActionResp(BaseModel):
    ok: bool
