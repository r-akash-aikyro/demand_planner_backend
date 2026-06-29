import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ForecastSession, Forecast
from app.models import ApprovalHistory


class ForecastService:
    def __init__(self, db: AsyncSession, company_id: str):
        self.db = db
        self.company_id = company_id

    async def create_session(self, data, user_id: str) -> ForecastSession:
        sid = uuid.uuid4().hex
        sess = ForecastSession(
            session_id=sid, company_id=self.company_id,
            dataset_name=data.dataset_name, horizon=data.horizon,
            aggregation=data.aggregation, status="draft",
            generated_by=user_id,
        )
        self.db.add(sess)
        await self.db.flush()
        return sess

    async def get_session(self, session_id: str) -> ForecastSession | None:
        return (
            await self.db.execute(
                select(ForecastSession).where(
                    ForecastSession.session_id == session_id,
                    ForecastSession.company_id == self.company_id,
                )
            )
        ).scalar_one_or_none()

    async def list_sessions(self):
        return (
            await self.db.execute(
                select(ForecastSession)
                .where(ForecastSession.company_id == self.company_id)
                .order_by(ForecastSession.created_at.desc())
            )
        ).scalars().all()

    async def forecast_rows(self, session_id: str, product_id: str | None = None):
        stmt = select(Forecast).where(
            Forecast.company_id == self.company_id,
            Forecast.session_id == session_id,
        )
        if product_id:
            stmt = stmt.where(Forecast.product_id == product_id)
        return (await self.db.execute(stmt.order_by(Forecast.date))).scalars().all()

    async def publish(self, session_id: str, user_id: str) -> ForecastSession:
        sess = await self.get_session(session_id)
        if not sess:
            raise ValueError("Session not found")
        sess.status = "published"
        sess.published_at = datetime.now(timezone.utc)
        self.db.add(ApprovalHistory(
            company_id=self.company_id, entity_type="forecast",
            entity_id=session_id, action="published", user_id=user_id,
        ))
        await self.db.flush()
        return sess

    async def mark_generated(self, session_id: str, summary: dict):
        sess = await self.get_session(session_id)
        if not sess:
            return
        sess.model_used = summary.get("model_used")
        sess.sku_count = summary.get("sku_count", 0)
        sess.row_count = summary.get("row_count", 0)
        sess.metrics = summary.get("metrics")
        sess.generated_at = datetime.now(timezone.utc)
        await self.db.flush()
