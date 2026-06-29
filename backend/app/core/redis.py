import redis.asyncio as aioredis
from app.core.config import settings

redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def blacklist_token(jti: str, ttl: int) -> None:
    await redis_client.setex(f"bl:{jti}", ttl, "1")


async def is_blacklisted(jti: str) -> bool:
    return bool(await redis_client.exists(f"bl:{jti}"))
