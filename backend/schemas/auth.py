from pydantic import BaseModel, EmailStr, Field


class RegisterReq(BaseModel):
    email: EmailStr
    nickname: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=6, max_length=64)


class LoginReq(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=64)


class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int