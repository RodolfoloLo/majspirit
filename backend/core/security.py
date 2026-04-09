from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as exc:
        raise ValueError("invalid token") from exc

#jose 是一个 Python 库，用于处理 JSON Web Tokens (JWT)。它提供了编码和解码 JWT 的功能，支持多种加密算法。在这个项目中，我们使用 jose 来创建和验证 JWT，以实现用户认证和授权。
#JWT鉴权过程: 1. 客户端使用用户名和密码登录，服务器验证后返回 JWT；2. 客户端在后续请求中携带 JWT；3. 服务器解码 JWT 并验证其有效性；4. 如果 JWT 有效，服务器处理请求并返回响应。
#客户端后续请求怎么就能携带 JWT 了呢？通常是在登录成功后，服务器会将 JWT 返回给客户端，客户端可以将其存储在浏览器的 localStorage、sessionStorage 或者 cookie 中.