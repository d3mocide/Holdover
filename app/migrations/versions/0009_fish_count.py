"""fish_count: adult fish passage counts (DART, Willamette Falls)

Revision ID: 0009
Revises: 0008
"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fish_count",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project", sa.Text(), nullable=False),
        sa.Column("observed_on", sa.Text(), nullable=False),
        sa.Column("species", sa.Text(), nullable=False),
        sa.Column("count", sa.Float(), nullable=False),
        sa.Column("avg10", sa.Float()),
        sa.Column("raw_fetch_id", sa.Integer()),
    )
    op.create_index("ix_fish_count_observed_on", "fish_count", ["observed_on"])
    op.create_index("ix_fish_count_key", "fish_count", ["project", "observed_on", "species", "id"])


def downgrade() -> None:
    op.drop_table("fish_count")
