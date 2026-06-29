import json
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import DataUpload, Lookup
from app.core.redis import redis_client
from app.core.config import settings


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


class DashboardService:
    def __init__(self, db: AsyncSession, company_id: str):
        self.db = db
        self.company_id = company_id

    async def _all_rows(self) -> list[dict]:
        uploads = (
            await self.db.execute(
                select(DataUpload).where(DataUpload.company_id == self.company_id)
            )
        ).scalars().all()
        rows: list[dict] = []
        for u in uploads:
            rows.extend(u.data or [])
        return rows

    async def _lookup(self) -> list[Lookup]:
        return (
            await self.db.execute(select(Lookup).where(Lookup.company_id == self.company_id))
        ).scalars().all()

    def _match(self, row, lk_by_product, filters) -> bool:
        if not filters:
            return True
        meta = lk_by_product.get(str(row.get("product_id")))
        if not meta:
            return False
        for k, v in filters.items():
            if v and getattr(meta, k, None) != v:
                return False
        return True

    async def kpis(self, filters: dict) -> dict:
        cache_key = f"kpis:{self.company_id}:{json.dumps(filters, sort_keys=True)}"
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

        rows = await self._all_rows()
        lookup = await self._lookup()
        lk_by_product = {l.product_id: l for l in lookup}

        total_qty = total_rev = 0.0
        skus, locations = set(), set()
        monthly = defaultdict(float)
        for r in rows:
            if not self._match(r, lk_by_product, filters):
                continue
            total_qty += _num(r.get("quantity"))
            total_rev += _num(r.get("revenue"))
            if r.get("product_id"):
                skus.add(str(r["product_id"]))
            if r.get("location_id"):
                locations.add(str(r["location_id"]))
            d = str(r.get("date") or "")[:7]
            if d:
                monthly[d] += _num(r.get("quantity"))

        result = {
            "total_quantity": round(total_qty, 2),
            "total_revenue": round(total_rev, 2),
            "sku_count": len(skus),
            "location_count": len(locations) or len({l.location_id for l in lookup}),
            "monthly_volume": [
                {"month": m, "quantity": round(q, 2)} for m, q in sorted(monthly.items())
            ],
        }
        await redis_client.setex(cache_key, settings.KPI_CACHE_TTL, json.dumps(result))
        return result

    async def filters(self) -> dict:
        lookup = await self._lookup()
        def uniq(attr):
            return sorted({getattr(l, attr) for l in lookup if getattr(l, attr)})
        return {
            "category": uniq("category"),
            "brand": uniq("brand"),
            "state": uniq("state"),
            "region": uniq("region"),
            "channel": uniq("channel"),
            "location_id": uniq("location_id"),
        }
