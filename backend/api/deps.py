from fastapi import Depends
# HTTPAuthorizationCredentials：解析后的认证信息，包含Token
# HTTPBearer：用来自动从请求头中提取Bearer Token的工具
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import decode_access_token
from backend.db.session import get_db
from backend.exceptions.business import InvalidToken, NotAuthenticated, UserNotFound
from backend.repositories.user_repo import UserRepo

# 创建Bearer认证的实例
# auto_error=False：如果请求里没有认证信息，不要抛出FastAPI的默认错误，我们要自己抛自定义的业务异常
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    #通过bearer_scheme自动从请求头中提取认证信息
    db: AsyncSession = Depends(get_db, use_cache=False),
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
