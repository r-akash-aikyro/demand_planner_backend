from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.core.redis import is_blacklisted
from app.db.session import get_db

bearer = HTTPBearer(auto_error=True)

ROLE_RANK = {"viewer": 0, "analyst": 1, "planner": 2, "admin": 3}


@dataclass
class CurrentUser:
    id: str
    company_id: str
    role: str


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> CurrentUser:
    try:
        payload = decode_token(creds.credentials)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")
    if await is_blacklisted(payload.get("jti", "")):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token revoked")
    return CurrentUser(
        id=payload["sub"], company_id=payload["company_id"], role=payload["role"]
    )


def require_role(*roles: str):
    async def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user
    return _check


def min_role(role: str):
    threshold = ROLE_RANK[role]

    async def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if ROLE_RANK.get(user.role, -1) < threshold:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user
    return _check


DB = AsyncSession
