"""gear: gear_item, gear_setup; gear references on trip and catch

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gear_item",
        sa.Column("uuid", sa.Text(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("user.id")),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("brand", sa.Text()),
        sa.Column("model", sa.Text()),
        sa.Column("size", sa.Text()),
        sa.Column("color", sa.Text()),
        sa.Column("quantity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("fisheries_json", sa.Text()),
        sa.Column("status", sa.Text(), server_default="active", nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("photo_path", sa.Text()),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index("ix_gear_item_owner_id", "gear_item", ["owner_id"])
    op.create_table(
        "gear_setup",
        sa.Column("uuid", sa.Text(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("user.id")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("item_uuids_json", sa.Text(), server_default="[]", nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index("ix_gear_setup_owner_id", "gear_setup", ["owner_id"])
    with op.batch_alter_table("trip") as b:
        b.add_column(sa.Column("setup_uuid", sa.Text()))
        b.add_column(sa.Column("gear_json", sa.Text()))
    with op.batch_alter_table("catch") as b:
        b.add_column(sa.Column("gear_uuid", sa.Text()))


def downgrade() -> None:
    with op.batch_alter_table("catch") as b:
        b.drop_column("gear_uuid")
    with op.batch_alter_table("trip") as b:
        b.drop_column("gear_json")
        b.drop_column("setup_uuid")
    op.drop_index("ix_gear_setup_owner_id", table_name="gear_setup")
    op.drop_table("gear_setup")
    op.drop_index("ix_gear_item_owner_id", table_name="gear_item")
    op.drop_table("gear_item")
