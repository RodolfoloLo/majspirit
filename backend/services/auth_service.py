from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.security import create_access_token, hash_password, verify_password
from backend.exceptions.business import EmailAlreadyExists, InvalidCredentials
from backend.repositories.user_repo import UserRepo
from backend.schemas.auth import LoginReq, RegisterReq, TokenResp

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepo(db)

    async def register(self, payload: RegisterReq) -> TokenResp:
        async with self.db.begin():
            exists = await self.repo.get_by_email(payload.email)
            if exists:
                raise EmailAlreadyExists()

            user = await self.repo.create(
                email=payload.email,
                nickname=payload.nickname,
                password_hash=hash_password(payload.password),
            )
        token = create_access_token(user.id)
        return TokenResp(access_token=token, expires_in=settings.JWT_EXPIRE_MINUTES * 60)

    async def login(self, payload: LoginReq) -> TokenResp:
        async with self.db.begin():
            user = await self.repo.get_by_email(payload.email)
            if not user:
                raise InvalidCredentials()

            if not verify_password(payload.password, user.password_hash):
                raise InvalidCredentials()

            await self.repo.update_last_login(user)
        token = create_access_token(user.id)
        return TokenResp(access_token=token, expires_in=settings.JWT_EXPIRE_MINUTES * 60)