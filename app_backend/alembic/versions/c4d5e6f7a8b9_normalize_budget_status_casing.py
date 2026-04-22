"""normalize budget status casing

Revision ID: c4d5e6f7a8b9
Revises: b243458ed40d
Create Date: 2026-04-22

Production audit found the `budgets.status` column had a mix of 'active' and
'ACTIVE' (16 lowercase + 65 uppercase). No live filter currently relies on
either case so nothing is broken, but the inconsistency is a foot-gun the
moment anyone writes a ``WHERE status = 'ACTIVE'`` query.

Standardising on UPPERCASE matches the convention already in place for
work_orders (see d2f3e4a5b6c7) and users.

Idempotent — safe to re-run.
"""

from alembic import op


revision = "c4d5e6f7a8b9"
down_revision = "b243458ed40d"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE budgets SET status = 'ACTIVE'    WHERE status = 'active'")
    op.execute("UPDATE budgets SET status = 'FROZEN'    WHERE status = 'frozen'")
    op.execute("UPDATE budgets SET status = 'CLOSED'    WHERE status = 'closed'")
    op.execute("UPDATE budgets SET status = 'CANCELLED' WHERE status = 'cancelled'")


def downgrade():
    # No-op: lossy in the same way d2f3e4a5b6c7 documents.
    pass
