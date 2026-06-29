from fastapi import APIRouter
from sqlalchemy import text
from app.db.session import engine
from app.core.redis import redis_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    db_ok = redis_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    try:
        redis_ok = bool(await redis_client.ping())
    except Exception:
        pass
    status = "ok" if (db_ok and redis_ok) else "degraded"
    return {"status": status, "db": db_ok, "redis": redis_ok}
