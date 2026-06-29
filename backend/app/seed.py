"""Seed a demo company + admin user. Run: python -m app.seed"""
import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import Company, User, Role
from app.core.security import hash_password

DEMO_EMAIL = "admin@demo.com"
DEMO_PASSWORD = "admin123"


async def seed():
    async with SessionLocal() as db:
        for name in ("admin", "planner", "analyst", "viewer"):
            exists = (await db.execute(select(Role).where(Role.name == name))).scalar_one_or_none()
            if not exists:
                db.add(Role(name=name, permissions={}))
        existing = (await db.execute(select(User).where(User.email == DEMO_EMAIL))).scalar_one_or_none()
        if existing:
            print("Demo user already exists:", DEMO_EMAIL)
            await db.commit()
            return
        company = Company(name="Demo Company")
        db.add(company)
        await db.flush()
        db.add(User(company_id=company.id, email=DEMO_EMAIL,
                    password_hash=hash_password(DEMO_PASSWORD),
                    role="admin", full_name="Demo Admin"))
        await db.commit()
        print(f"Seeded company + admin: {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
