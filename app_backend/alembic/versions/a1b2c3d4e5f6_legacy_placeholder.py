"""legacy placeholder — original migration file lost, schema already applied to DB

Revision ID: a1b2c3d4e5f6
Revises: None
Create Date: 2026-04-20

Background
----------
The original ``a1b2c3d4e5f6`` migration file was applied directly to production
databases at some point in the past but never committed to git. Subsequent
migrations (``9f2b7c4d1eaa`` and onwards) reference it as their parent, which
made every later ``alembic`` invocation crash with::

    KeyError: 'a1b2c3d4e5f6'

This placeholder reinstates the revision *as a no-op root* so the chain parses
cleanly. It does NOT attempt to re-apply whatever the original DDL was — that
work has already been done in production. If you ever need to bootstrap a
fresh database, you'll need to add the missing DDL here, or rely on
``create_all_missing_tables.py`` which builds the full schema from scratch.
"""

revision = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # No-op — schema was applied out-of-band before the file was lost.
    pass


def downgrade():
    # No-op — we don't know what the original DDL was, so we can't reverse it.
    pass
