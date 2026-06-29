from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Override, Forecast, ApprovalHistory, User
from app.core.deps import ROLE_RANK


def required_rank(pct: float) -> int:
    """Approval tier → minimum role rank. 0-10 auto, 10-25 planner, >25 admin."""
    pct = abs(pct)
    if pct <= 10:
        return ROLE_RANK["viewer"]    # auto — anyone
    if pct <= 25:
        return ROLE_RANK["planner"]   # manager
    return ROLE_RANK["admin"]         # manager+director / executive


class OverrideService:
    def __init__(self, db: AsyncSession, company_id: str):
        self.db = db
        self.company_id = company_id

    async def _forecast(self, fid: str) -> Forecast | None:
        return (await self.db.execute(
            select(Forecast).where(Forecast.id == fid, Forecast.company_id == self.company_id)
        )).scalar_one_or_none()

    async def _get(self, oid: str) -> Override | None:
        return (await self.db.execute(
            select(Override).where(Override.id == oid, Override.company_id == self.company_id)
        )).scalar_one_or_none()

    async def _admin_email(self) -> str | None:
        u = (await self.db.execute(
            select(User).where(User.company_id == self.company_id, User.role == "admin")
        )).scalars().first()
        return u.email if u else None

    async def create(self, data, user_id: str) -> tuple[Override, str | None]:
        fc = await self._forecast(data.forecast_id)
        if not fc:
            raise ValueError("Forecast not found")
        original = float(fc.forecast_value)
        pct = ((data.override_value - original) / original * 100) if original else 0.0
        auto = abs(pct) <= 10
        ov = Override(
            company_id=self.company_id, forecast_id=fc.id, product_id=fc.product_id,
            user_id=user_id, original_value=original, override_value=data.override_value,
            pct_change=round(pct, 2), reason=data.reason,
            status="approved" if auto else "pending",
        )
        self.db.add(ov)
        await self.db.flush()
        self.db.add(ApprovalHistory(
            company_id=self.company_id, entity_type="override", entity_id=str(ov.id),
            action="created", user_id=user_id,
            new_value={"override_value": data.override_value, "pct": round(pct, 2)},
        ))
        if auto:
            await self._apply(ov)
            notify_email = None
        else:
            notify_email = await self._admin_email()
        await self.db.flush()
        return ov, notify_email

    async def _apply(self, ov: Override):
        fc = await self._forecast(str(ov.forecast_id))
        if fc:
            fc.forecast_value = ov.override_value
            fc.forecast_type = "override"

    async def decide(self, oid: str, approver, approve: bool, comments) -> Override:
        ov = await self._get(oid)
        if not ov:
            raise ValueError("Override not found")
        if ov.status != "pending":
            raise ValueError("Override not pending")
        if ROLE_RANK.get(approver.role, -1) < required_rank(float(ov.pct_change or 0)):
            raise ValueError("Insufficient role to approve this change")
        ov.status = "approved" if approve else "rejected"
        ov.approved_by = approver.id
        from datetime import datetime, timezone
        ov.approved_at = datetime.now(timezone.utc)
        if approve:
            await self._apply(ov)
        self.db.add(ApprovalHistory(
            company_id=self.company_id, entity_type="override", entity_id=str(ov.id),
            action="approved" if approve else "rejected", user_id=approver.id,
            comments=comments,
        ))
        await self.db.flush()
        return ov

    async def list(self, status: str | None = None):
        stmt = select(Override).where(Override.company_id == self.company_id)
        if status:
            stmt = stmt.where(Override.status == status)
        return (await self.db.execute(stmt.order_by(Override.created_at.desc()))).scalars().all()
