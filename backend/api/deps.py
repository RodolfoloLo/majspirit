from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import decode_access_token
from backend.db.session import get_db
from backend.exceptions.business import InvalidToken, NotAuthenticated, UserNotFound
from backend.repositories.user_repo import UserRepo


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        raise NotAuthenticated()

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise InvalidToken()

    user = await UserRepo(db).get_by_id(user_id)
    if not user:
        raise UserNotFound()

    return user
