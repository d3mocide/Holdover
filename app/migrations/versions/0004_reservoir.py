"""reservoir_reading: Army Corps pool elevations

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reservoir_reading",
        sa.Column("project", sa.Text(), nullable=False),
        sa.Column("observed_at", sa.Text(), nullable=False),
        sa.Column("elevation_ft", sa.Float(), nullable=False),
        sa.Column("raw_fetch_id", sa.Integer()),
        sa.PrimaryKeyConstraint("project", "observed_at"),
    )


def downgrade() -> None:
    op.drop_table("reservoir_reading")
