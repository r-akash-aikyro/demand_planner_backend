import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, UUIDMixin, TimestampMixin


class Override(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "overrides"
    company_id: Mapped[str] = mapped_column(String(50))
    forecast_id: Mapped[str] = mapped_column(String(50))
    product_id: Mapped[str] = mapped_column(String(120))
    user_id: Mapped[str] = mapped_column(String(50))
    original_value: Mapped[float] = mapped_column(Numeric)
    override_value: Mapped[float] = mapped_column(Numeric)
    pct_change: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    approved_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ApprovalHistory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "approval_history"
    company_id: Mapped[str] = mapped_column(String(50))
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(40))
    user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    comments: Mapped[str | None] = mapped_column(String, nullable=True)
    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
