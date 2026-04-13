import redis.asyncio as redis

from backend.core.config import settings


redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.redis_password or None,
    decode_responses=True,
)