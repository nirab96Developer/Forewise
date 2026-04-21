"""add NEEDS_RE_COORDINATION work order status

Revision ID: c3d5e6f7a8b9
Revises: b2c4d5e6f7a8
Create Date: 2026-04-13

Used when a field worker scans equipment that does not match the order
(scenario C in equipment intake). The work order goes back to the coordinator
for a decision (re-distribute / admin override / cancel). Field operations
(scan / worklog) are blocked while in this status.
"""

from alembic import op


revision = "c3d5e6f7a8b9"
down_revision = "b2c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade():
    """Insert lookup row. Idempotent — safe to re-run."""
    op.execute(
        """
        INSERT INTO work_order_statuses (code, name, description, is_active, display_order, created_at, updated_at)
        SELECT
            'NEEDS_RE_COORDINATION',
            'ממתין לבדיקת מתאם — סוג כלי שגוי',
            'הזמנה הוחזרה למתאם לאחר שמנהל עבודה סרק כלי בסוג שונה מהמוזמן. נדרשת החלטה: הפצה מחדש, אישור חריג, או ביטול.',
            TRUE,
            65,
            NOW(),
            NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM work_order_statuses WHERE code = 'NEEDS_RE_COORDINATION'
        )
        """
    )


def downgrade():
    op.execute(
        """
        DELETE FROM work_order_statuses WHERE code = 'NEEDS_RE_COORDINATION'
        """
    )
