from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User

#利用写一个class UserRepo来封装对User模型的数据库操作，这样可以将数据库访问逻辑与业务逻辑分离，提高代码的可维护性和可测试性。
#这其实相当于把crud操作封装在一个类里，其他地方需要对User模型进行数据库操作时，就可以通过这个类来调用对应的方法，而不需要直接操作数据库session。这种设计模式在很多web框架中都很常见，可以提高代码的组织性和可读性。
class UserRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, email: str, nickname: str, password_hash: str) -> User:
        user = User(email=email, nickname=nickname, password_hash=password_hash)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_last_login(self, user: User) -> None:
        from datetime import datetime, timezone

        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()