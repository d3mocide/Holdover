"""Public seasonal flow cache; does not alter readings or personal data."""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("flow_baseline",
        sa.Column("gauge_id", sa.Integer(), sa.ForeignKey("gauge.id"), primary_key=True),
        sa.Column("payload_json", sa.Text()), sa.Column("fetched_at", sa.Text()),
        sa.Column("attempted_at", sa.Text(), nullable=False), sa.Column("error", sa.Text()))


def downgrade() -> None:
    op.drop_table("flow_baseline")
