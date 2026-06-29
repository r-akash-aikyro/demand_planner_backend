import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(p: str) -> str:
    return pwd_context.hash(p)


def verify_password(p: str, hashed: str) -> bool:
    return pwd_context.verify(p, hashed)


def _token(sub: str, company_id: str, role: str, ttl: int, kind: str) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub, "company_id": company_id, "role": role,
        "type": kind, "jti": jti,
        "iat": now, "exp": now + timedelta(seconds=ttl),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG), jti


def create_access_token(sub, company_id, role):
    return _token(sub, company_id, role, settings.ACCESS_TTL, "access")


def create_refresh_token(sub, company_id, role):
    return _token(sub, company_id, role, settings.REFRESH_TTL, "refresh")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except JWTError as e:
        raise ValueError(str(e))
