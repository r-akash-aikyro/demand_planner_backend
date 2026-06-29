import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, UUIDMixin, TimestampMixin


class SourceConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "source_configs"
    company_id: Mapped[str] = mapped_column(String(50))
    file_name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(50))
    column_mappings: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class DataUpload(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "data_uploads"
    company_id: Mapped[str] = mapped_column(String(50))
    source_config_id: Mapped[str] = mapped_column(String(50))
    upload_date: Mapped[str | None] = mapped_column(String(40), nullable=True)
    row_count: Mapped[int] = mapped_column(default=0)
    data: Mapped[list] = mapped_column(JSONB, default=list)


class Lookup(Base, UUIDMixin):
    __tablename__ = "lookup"
    company_id: Mapped[str] = mapped_column(String(50))
    product_id: Mapped[str] = mapped_column(String(120))
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(120), nullable=True)
    location_id: Mapped[str] = mapped_column(String(120))
    location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
