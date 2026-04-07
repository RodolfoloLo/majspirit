from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.security import create_access_token, hash_password, verify_password
from backend.repositories.user_repo import UserRepo
from backend.schemas.auth import LoginReq, RegisterReq, TokenResp


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepo(db)

    async def register(self, payload: RegisterReq) -> TokenResp:
        exists = await self.repo.get_by_email(payload.email)
        if exists:
            raise ValueError("email already exists")

        user = await self.repo.create(
            email=payload.email,
            nickname=payload.nickname,
            password_hash=hash_password(payload.password),
        )
        token = create_access_token(user.id)
        return TokenResp(access_token=token, expires_in=settings.JWT_EXPIRE_MINUTES * 60)

    async def login(self, payload: LoginReq) -> TokenResp:
        user = await self.repo.get_by_email(payload.email)
        if not user:
            raise ValueError("invalid credentials")

        if not verify_password(payload.password, user.password_hash):
            raise ValueError("invalid credentials")

        await self.repo.update_last_login(user)
        token = create_access_token(user.id)
        return TokenResp(access_token=token, expires_in=settings.JWT_EXPIRE_MINUTES * 60)