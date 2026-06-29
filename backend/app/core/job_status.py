"""Forecast job status in Redis: forecast:{session_id}:status."""
from app.core.redis import redis_client

RUNNING, COMPLETE, ERROR = "running", "complete", "error"


def _key(session_id: str) -> str:
    return f"forecast:{session_id}:status"


async def set_status(session_id: str, status: str, ttl: int = 86400) -> None:
    await redis_client.setex(_key(session_id), ttl, status)


async def get_status(session_id: str) -> str | None:
    return await redis_client.get(_key(session_id))
