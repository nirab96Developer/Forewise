"""update worklog vat default to 0.18

Revision ID: 9f2b7c4d1eaa
Revises: a1b2c3d4e5f6
Create Date: 2026-03-29
"""

from alembic import op


revision = "9f2b7c4d1eaa"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        ALTER TABLE worklogs
        ALTER COLUMN vat_rate SET DEFAULT 0.18
        """
    )


def downgrade():
    op.execute(
        """
        ALTER TABLE worklogs
        ALTER COLUMN vat_rate SET DEFAULT 0.17
        """
    )
