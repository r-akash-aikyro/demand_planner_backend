from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import SourceConfig, DataUpload, Lookup
from app.schemas.importing import LOOKUP_COLUMNS


def _apply_mapping(rows: list[dict], mapping: dict[str, str]) -> list[dict]:
    """Map user columns -> canonical, deriving revenue = price*quantity if absent."""
    out = []
    for r in rows:
        canon = {}
        for canonical, user_col in mapping.items():
            if user_col in r:
                canon[canonical] = r[user_col]
        if not canon.get("revenue") and canon.get("price") and canon.get("quantity"):
            try:
                canon["revenue"] = float(canon["price"]) * float(canon["quantity"])
            except (TypeError, ValueError):
                pass
        out.append(canon)
    return out


class ImportService:
    def __init__(self, db: AsyncSession, company_id: str):
        self.db = db
        self.company_id = company_id

    async def list_sources(self):
        return (
            await self.db.execute(
                select(SourceConfig).where(SourceConfig.company_id == self.company_id)
            )
        ).scalars().all()

    async def create_source(self, data) -> SourceConfig:
        sc = SourceConfig(
            company_id=self.company_id, file_name=data.file_name,
            file_type=data.file_type, column_mappings=data.column_mappings,
        )
        self.db.add(sc)
        await self.db.flush()
        return sc

    async def _get_source(self, source_id: str) -> SourceConfig | None:
        return (
            await self.db.execute(
                select(SourceConfig).where(
                    SourceConfig.id == source_id,
                    SourceConfig.company_id == self.company_id,
                )
            )
        ).scalar_one_or_none()

    async def update_mapping(self, source_id: str, mappings: dict) -> SourceConfig:
        sc = await self._get_source(source_id)
        if not sc:
            raise ValueError("Source config not found")
        sc.column_mappings = mappings
        await self.db.flush()
        return sc

    async def import_data(self, source_id: str, rows: list[dict], upload_date) -> DataUpload:
        sc = await self._get_source(source_id)
        if not sc:
            raise ValueError("Source config not found")
        canonical = _apply_mapping(rows, sc.column_mappings)
        upload = DataUpload(
            company_id=self.company_id, source_config_id=sc.id,
            upload_date=upload_date, row_count=len(canonical), data=canonical,
        )
        self.db.add(upload)
        await self.db.flush()
        return upload

    async def import_lookup(self, rows: list[dict], mapping: dict) -> int:
        mapped = []
        for r in rows:
            entry = {c: r.get(mapping.get(c)) for c in LOOKUP_COLUMNS if mapping.get(c) in r}
            if entry.get("product_id") and entry.get("location_id"):
                mapped.append(entry)
        # replace existing lookup for this company (fresh master each import)
        await self.db.execute(delete(Lookup).where(Lookup.company_id == self.company_id))
        for e in mapped:
            self.db.add(Lookup(company_id=self.company_id, **e))
        await self.db.flush()
        return len(mapped)
