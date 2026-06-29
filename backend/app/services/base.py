from typing import Generic, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseService(Generic[T]):
    """Company-scoped CRUD base. Every query filtered by company_id."""
    model: type

    def __init__(self, db: AsyncSession, company_id: str):
        self.db = db
        self.company_id = company_id

    def _scope(self, stmt):
        return stmt.where(self.model.company_id == self.company_id)

    async def list(self, limit: int = 50, offset: int = 0):
        stmt = self._scope(select(self.model)).limit(limit).offset(offset)
        return (await self.db.execute(stmt)).scalars().all()

    async def get(self, id_):
        stmt = self._scope(select(self.model)).where(self.model.id == id_)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def create(self, **kwargs):
        obj = self.model(company_id=self.company_id, **kwargs)
        self.db.add(obj)
        await self.db.flush()
        return obj
