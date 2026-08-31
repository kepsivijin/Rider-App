"""add passenger capacity and ride vehicle fields

Revision ID: b7e2c1a9d004
Revises: 0c22d24fa530
Create Date: 2026-08-31
"""
from alembic import op

revision = "b7e2c1a9d004"
down_revision = "0c22d24fa530"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE drivers ADD COLUMN IF NOT EXISTS passenger_capacity INTEGER NOT NULL DEFAULT 1")
    op.execute("ALTER TABLE rides ADD COLUMN IF NOT EXISTS passenger_count INTEGER NOT NULL DEFAULT 1")
    op.execute("ALTER TABLE rides ADD COLUMN IF NOT EXISTS vehicle_type VARCHAR(20) NOT NULL DEFAULT 'bike'")


def downgrade() -> None:
    op.execute("ALTER TABLE rides DROP COLUMN IF EXISTS vehicle_type")
    op.execute("ALTER TABLE rides DROP COLUMN IF EXISTS passenger_count")
    op.execute("ALTER TABLE drivers DROP COLUMN IF EXISTS passenger_capacity")
