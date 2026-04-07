from datetime import datetime

from pydantic import BaseModel, EmailStr,ConfigDict


class UserResp(BaseModel):
    id: int
    email: EmailStr
    nickname: str
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )