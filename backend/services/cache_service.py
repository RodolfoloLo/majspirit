import json

from backend.utils.redis_client import redis_client


class CacheService:
    #获取指定键的值并解析为JSON对象,如果键不存在则返回None.
    async def get_json(self, key: str):
        raw = await redis_client.get(key)
        return json.loads(raw) if raw else None

    #将一个Python对象序列化为JSON字符串并存储在指定键下,可以设置过期时间(单位:秒).
    async def set_json(self, key: str, value: dict, ttl_seconds: int = 300):
        await redis_client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl_seconds)

    async def delete(self, key: str):
        await redis_client.delete(key)

#redis_client基本操作:
#get(key):获取指定键的值,如果键不存在则返回None.
#set(key, value, ex=ttl_seconds):将一个值存储在指定键下,可以设置过期时间(单位:秒).
#delete(key):删除指定键及其值.

#Redis搭配json json.dumps和json.loads可以实现Python对象的序列化和反序列化,方便地存储和读取复杂数据结构.