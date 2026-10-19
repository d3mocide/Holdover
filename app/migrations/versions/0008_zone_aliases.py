"""Stocking aliases are per zone: ODFW labels repeat across zones (LOST LAKE is in Central and the Northwest)

Revision ID: 0008
Revises: 0007
"""
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Aliases that point at a waterbody outside Willamette move to that zone's namespace. Willamette keeps the original name.
    op.execute("""
        UPDATE waterbody_alias SET source = 'odfw_stocking:' || (SELECT zone FROM waterbody WHERE waterbody.id = waterbody_alias.waterbody_id)
        WHERE source = 'odfw_stocking' AND waterbody_id IN (SELECT id FROM waterbody WHERE zone <> 'willamette')
    """)


def downgrade() -> None:
    op.execute("UPDATE waterbody_alias SET source = 'odfw_stocking' WHERE source LIKE 'odfw_stocking:%'")
