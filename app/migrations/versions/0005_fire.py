"""fire_danger and fire_nearby: ODF fire danger and NIFC perimeters, per waterbody per fetch

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fire_danger",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("waterbody_id", sa.Integer(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("area", sa.Text(), nullable=False),
        sa.Column("district", sa.Integer()),
        sa.Column("raw_fetch_id", sa.Integer()),
    )
    op.create_index("ix_fire_danger_waterbody_id", "fire_danger", ["waterbody_id"])
    op.create_index("ix_fire_danger_raw_fetch_id", "fire_danger", ["raw_fetch_id"])
    op.create_table(
        "fire_nearby",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("waterbody_id", sa.Integer(), nullable=False),
        sa.Column("incident", sa.Text(), nullable=False),
        sa.Column("acres", sa.Float()),
        sa.Column("percent_contained", sa.Float()),
        sa.Column("updated_at", sa.Text()),
        sa.Column("distance_km", sa.Float(), nullable=False),
        sa.Column("inside", sa.Integer(), server_default="0", nullable=False),
        sa.Column("raw_fetch_id", sa.Integer()),
    )
    op.create_index("ix_fire_nearby_waterbody_id", "fire_nearby", ["waterbody_id"])
    op.create_index("ix_fire_nearby_raw_fetch_id", "fire_nearby", ["raw_fetch_id"])


def downgrade() -> None:
    op.drop_table("fire_nearby")
    op.drop_table("fire_danger")
