"""normalize work order status casing

Revision ID: d2f3e4a5b6c7
Revises: d1e2f3a4b5c6
Create Date: 2026-04-18

The work_order_service used to write status='completed' (lowercase) from
``close()`` and 'ACTIVE' from ``start()``. The live state machine elsewhere
uses UPPERCASE ('COMPLETED', 'IN_PROGRESS'), and the FE filters/labels assume
the same. This migration normalises any historical rows that were saved with
the old casing so dashboards and statistics start showing them correctly.

Idempotent — safe to re-run.
"""

from alembic import op


revision = "d2f3e4a5b6c7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE work_orders SET status='COMPLETED' WHERE status='completed'")
    op.execute("UPDATE work_orders SET status='IN_PROGRESS' WHERE status='ACTIVE'")
    # Other obsolete lowercase values that may have leaked in via the old service:
    op.execute("UPDATE work_orders SET status='PENDING'      WHERE status='pending'")
    op.execute("UPDATE work_orders SET status='DISTRIBUTING' WHERE status='sent_to_supplier'")
    op.execute("UPDATE work_orders SET status='SUPPLIER_ACCEPTED_PENDING_COORDINATOR' WHERE status='accepted'")
    op.execute("UPDATE work_orders SET status='REJECTED'  WHERE status='rejected'")
    op.execute("UPDATE work_orders SET status='IN_PROGRESS' WHERE status='in_progress'")
    op.execute("UPDATE work_orders SET status='CANCELLED' WHERE status='cancelled'")
    op.execute("UPDATE work_orders SET status='EXPIRED'   WHERE status='expired'")


def downgrade():
    # Intentional no-op: downgrade would lose information (we cannot tell which
    # row was originally 'ACTIVE' vs 'IN_PROGRESS' after the upgrade).
    pass
