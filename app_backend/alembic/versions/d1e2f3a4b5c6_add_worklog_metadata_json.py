"""add metadata_json column to worklogs

Revision ID: d1e2f3a4b5c6
Revises: c3d5e6f7a8b9
Create Date: 2026-04-18

The worklog service writes scan_flags + hours summary to ``metadata_json`` but
the column was missing from the table — every write was silently dropped (and
``Worklog(**dict)`` would raise when scan flags were populated). This adds the
column so reviewer-visible audit data is actually persisted.
"""

from alembic import op
import sqlalchemy as sa


revision = "d1e2f3a4b5c6"
down_revision = "c3d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "worklogs",
        sa.Column("metadata_json", sa.Unicode(), nullable=True),
    )


def downgrade():
    op.drop_column("worklogs", "metadata_json")
