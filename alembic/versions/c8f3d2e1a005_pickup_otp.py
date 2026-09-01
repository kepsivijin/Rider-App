"""add pickup otp verification

Revision ID: c8f3d2e1a005
Revises: b7e2c1a9d004
"""
from alembic import op

revision = "c8f3d2e1a005"
down_revision = "b7e2c1a9d004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE rides ADD COLUMN IF NOT EXISTS pickup_otp VARCHAR(6)")
    op.execute("ALTER TABLE rides ADD COLUMN IF NOT EXISTS pickup_verified BOOLEAN NOT NULL DEFAULT false")


def downgrade() -> None:
    op.execute("ALTER TABLE rides DROP COLUMN IF EXISTS pickup_verified")
    op.execute("ALTER TABLE rides DROP COLUMN IF EXISTS pickup_otp")
