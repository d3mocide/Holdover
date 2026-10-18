"""accounts: user, session, invite, favorite; owner_id on journal tables

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("is_admin", sa.Integer(), server_default="0", nullable=False),
        sa.Column("disabled", sa.Integer(), server_default="0", nullable=False),
        sa.Column("home_lat", sa.Float()),
        sa.Column("home_lon", sa.Float()),
        sa.Column("created_at", sa.Text(), nullable=False),
    )
    op.create_table(
        "user_session",
        sa.Column("token_hash", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("last_used_at", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Text(), nullable=False),
        sa.Column("device", sa.Text()),
    )
    op.create_index("ix_user_session_user_id", "user_session", ["user_id"])
    op.create_table(
        "invite",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Text(), nullable=False),
        sa.Column("used_by", sa.Integer(), sa.ForeignKey("user.id")),
        sa.Column("used_at", sa.Text()),
    )
    op.create_table(
        "favorite",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("waterbody_id", sa.Integer(), sa.ForeignKey("waterbody.id", ondelete="CASCADE"), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "waterbody_id"),
    )
    # Existing journal rows predate accounts: owner stays NULL until the first admin is created and adopts them.
    for table in ("trip", "catch", "pin"):
        with op.batch_alter_table(table) as b:
            b.add_column(sa.Column("owner_id", sa.Integer(), sa.ForeignKey("user.id", name=f"fk_{table}_owner")))
            b.create_index(f"ix_{table}_owner_id", ["owner_id"])


def downgrade() -> None:
    for table in ("pin", "catch", "trip"):
        with op.batch_alter_table(table) as b:
            b.drop_index(f"ix_{table}_owner_id")
            b.drop_column("owner_id")
    op.drop_table("favorite")
    op.drop_table("invite")
    op.drop_index("ix_user_session_user_id", table_name="user_session")
    op.drop_table("user_session")
    op.drop_table("user")
