"""add invoice payment fields (paid_at, payment_reference, paid_by, sent_at)

Revision ID: b2c4d5e6f7a8
Revises: 9f2b7c4d1eaa
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa


revision = "b2c4d5e6f7a8"
down_revision = "9f2b7c4d1eaa"
branch_labels = None
depends_on = None


def upgrade():
    """Add audit fields for invoice payment lifecycle."""
    # paid_at — exact moment the invoice was marked as paid
    op.add_column(
        "invoices",
        sa.Column("paid_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_invoices_paid_at", "invoices", ["paid_at"])

    # payment_reference — bank transfer / cheque / receipt id
    op.add_column(
        "invoices",
        sa.Column("payment_reference", sa.Unicode(100), nullable=True),
    )

    # paid_by — user id of the accountant that confirmed payment
    op.add_column(
        "invoices",
        sa.Column("paid_by", sa.Integer(), nullable=True),
    )
    op.create_index("ix_invoices_paid_by", "invoices", ["paid_by"])

    # sent_at — when the invoice was actually pushed out to the supplier
    op.add_column(
        "invoices",
        sa.Column("sent_at", sa.DateTime(), nullable=True),
    )

    # Backfill paid_at for already-paid invoices (use updated_at as a best guess)
    op.execute(
        """
        UPDATE invoices
           SET paid_at = updated_at
         WHERE UPPER(status) = 'PAID' AND paid_at IS NULL
        """
    )


def downgrade():
    op.drop_index("ix_invoices_paid_by", table_name="invoices")
    op.drop_column("invoices", "paid_by")
    op.drop_column("invoices", "sent_at")
    op.drop_column("invoices", "payment_reference")
    op.drop_index("ix_invoices_paid_at", table_name="invoices")
    op.drop_column("invoices", "paid_at")
