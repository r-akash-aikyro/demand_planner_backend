import uuid
from datetime import datetime, date
from sqlalchemy import String, ForeignKey, Numeric, Date, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, UUIDMixin, TimestampMixin


class ForecastSession(Base, TimestampMixin):
    __tablename__ = "forecast_sessions"
    session_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    generated_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ModelingData(Base, UUIDMixin):
    __tablename__ = "modeling_data"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), index=True)
    company_id: Mapped[str] = mapped_column(String(50), index=True)
    data: Mapped[dict] = mapped_column(JSONB)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Forecast(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "forecasts"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), index=True)
    company_id: Mapped[str] = mapped_column(String(50), index=True)
    data: Mapped[dict] = mapped_column(JSONB)
    model_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentTrace(Base, UUIDMixin):
    __tablename__ = "agent_traces"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    agent_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="complete")
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
