import json

from backend.utils.redis_client import redis_client


class CacheService:
    async def get_json(self, key: str):
        raw = await redis_client.get(key)
        return json.loads(raw) if raw else None

    async def set_json(self, key: str, value: dict, ttl_seconds: int = 300):
        await redis_client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl_seconds)

    async def delete(self, key: str):
        await redis_client.delete(key)