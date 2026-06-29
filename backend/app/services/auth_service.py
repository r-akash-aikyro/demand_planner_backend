from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Company
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.core.redis import blacklist_token, is_blacklisted


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _by_email(self, email: str) -> User | None:
        return (
            await self.db.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()

    async def signup(self, data) -> User:
        if await self._by_email(data.email):
            raise ValueError("Email already registered")
        company = Company(name=data.company_name or "My Company")
        self.db.add(company)
        await self.db.flush()
        # first user of a new company is admin
        user = User(
            company_id=company.id, email=data.email,
            password_hash=hash_password(data.password),
            role="admin", full_name=data.full_name or data.email,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self._by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("User disabled")
        return user

    def issue_tokens(self, user: User):
        access, _ = create_access_token(str(user.id), str(user.company_id), user.role)
        refresh, _ = create_refresh_token(str(user.id), str(user.company_id), user.role)
        return access, refresh

    async def refresh(self, refresh_token: str):
        import time
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")
        jti = payload.get("jti", "")
        if await is_blacklisted(jti):
            raise ValueError("Refresh token revoked")
        # Rotate: revoke the consumed refresh token so it can't be replayed.
        await blacklist_token(jti, max(1, int(payload["exp"] - time.time())))
        access, _ = create_access_token(
            payload["sub"], payload["company_id"], payload["role"]
        )
        new_refresh, _ = create_refresh_token(
            payload["sub"], payload["company_id"], payload["role"]
        )
        return access, new_refresh

    async def logout(self, access_token: str, refresh_token: str | None = None):
        import time
        now = time.time()
        payload = decode_token(access_token)
        await blacklist_token(payload["jti"], max(1, int(payload["exp"] - now)))
        # Also revoke the refresh token if supplied, otherwise it stays valid for days.
        if refresh_token:
            try:
                rp = decode_token(refresh_token)
            except ValueError:
                return
            await blacklist_token(rp["jti"], max(1, int(rp["exp"] - now)))
