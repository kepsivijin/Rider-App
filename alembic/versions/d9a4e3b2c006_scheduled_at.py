"""add scheduled_at for plan-ahead rides

Revision ID: d9a4e3b2c006
Revises: c8f3d2e1a005
"""
from alembic import op

revision = "d9a4e3b2c006"
down_revision = "c8f3d2e1a005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE rides ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMP")


def downgrade() -> None:
    op.execute("ALTER TABLE rides DROP COLUMN IF EXISTS scheduled_at")
