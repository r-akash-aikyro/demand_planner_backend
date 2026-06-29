import uuid
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, UUIDMixin, TimestampMixin


class Company(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "companies"
    name: Mapped[str] = mapped_column(String(255))
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)


class Role(Base, UUIDMixin):
    __tablename__ = "roles"
    name: Mapped[str] = mapped_column(String(50))
    permissions: Mapped[dict] = mapped_column(JSONB, default=dict)


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"
    company_id: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="viewer")
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
