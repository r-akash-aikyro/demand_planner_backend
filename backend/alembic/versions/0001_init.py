"""baseline — create all tables from metadata

Revision ID: 0001_init
Revises:
Create Date: 2026-06-29
"""
from alembic import op
from app.db.base import Base
import app.models  # noqa: F401

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade():
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
