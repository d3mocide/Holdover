"""gauge.zone: which zone each gauge belongs to

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("gauge") as b:
        b.add_column(sa.Column("zone", sa.Text()))
    # every gauge that existed before this was a Willamette gauge
    op.execute("UPDATE gauge SET zone = 'willamette' WHERE zone IS NULL")


def downgrade() -> None:
    with op.batch_alter_table("gauge") as b:
        b.drop_column("zone")
