from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings


def _key(request):
    auth = request.headers.get("authorization", "")
    return auth[-32:] if auth else get_remote_address(request)


limiter = Limiter(key_func=_key, default_limits=[settings.RATE_LIMIT],
                  storage_uri=settings.REDIS_URL)
