from backend.core.config import settings
from backend.utils.redis_client import redis_client


async def check_rate_limit(user_key: str, limit: int | None = None, window_seconds: int = 60) -> bool:
    max_count = limit or settings.RATE_LIMIT_PER_MINUTE
    key = f"rl:{user_key}:{window_seconds}"
    try:
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, window_seconds)
        return count <= max_count
    except Exception:
        # Redis unavailable: fail-open to keep core game flow alive.
        return True