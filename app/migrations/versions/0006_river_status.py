"""river_status: NOAA NWPS flood category per mapped gauge, per fetch

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "river_status",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lid", sa.Text(), nullable=False),
        sa.Column("category", sa.Text()),
        sa.Column("stage_ft", sa.Float()),
        sa.Column("flow_kcfs", sa.Float()),
        sa.Column("valid_time", sa.Text()),
        sa.Column("fc_category", sa.Text()),
        sa.Column("fc_stage_ft", sa.Float()),
        sa.Column("fc_valid_time", sa.Text()),
        sa.Column("raw_fetch_id", sa.Integer()),
    )
    op.create_index("ix_river_status_lid", "river_status", ["lid"])
    op.create_index("ix_river_status_raw_fetch_id", "river_status", ["raw_fetch_id"])


def downgrade() -> None:
    op.drop_table("river_status")
