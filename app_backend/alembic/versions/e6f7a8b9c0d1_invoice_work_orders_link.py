"""invoice_work_orders link table + backfill from invoice_items

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-04-22

Phase 1.2 of the model-restructure roadmap.

Today the only way to know which work orders an invoice covers is the
3-hop chain `invoice → invoice_items.worklog_id → worklogs.work_order_id`.
This forces every consumer (mark-paid, dashboards, exports) to re-derive
the link, and made the recent budget-release fix have to fall back to a
clumsy "evenly split paid_amount across WOs" heuristic.

This migration adds an explicit `invoice_work_orders(invoice_id,
work_order_id, allocated_amount)` link table and back-fills it from the
existing line items so all downstream code can switch to a single join.

Idempotent — uses ON CONFLICT DO NOTHING semantics and skips table
creation if the table already exists.
"""

from alembic import op
import sqlalchemy as sa


revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "invoice_work_orders" not in inspector.get_table_names():
        op.create_table(
            "invoice_work_orders",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("invoice_id", sa.Integer,
                      sa.ForeignKey("invoices.id", ondelete="CASCADE"),
                      nullable=False, index=True),
            sa.Column("work_order_id", sa.Integer,
                      sa.ForeignKey("work_orders.id", ondelete="CASCADE"),
                      nullable=False, index=True),
            sa.Column("allocated_amount", sa.Numeric(18, 2), nullable=False,
                      server_default=sa.text("0")),
            # Audit
            sa.Column("created_at", sa.DateTime, nullable=False,
                      server_default=sa.text("NOW()")),
            sa.Column("updated_at", sa.DateTime, nullable=False,
                      server_default=sa.text("NOW()")),
            sa.Column("deleted_at", sa.DateTime, nullable=True),
            sa.Column("is_active", sa.Boolean, nullable=False,
                      server_default=sa.text("TRUE")),
            sa.Column("version", sa.Integer, nullable=False,
                      server_default=sa.text("1")),
            sa.UniqueConstraint("invoice_id", "work_order_id",
                                name="uq_invoice_wo"),
        )

    # Backfill: for each invoice, find the distinct WOs reached via
    # invoice_items.worklog_id → worklogs.work_order_id, summing the
    # invoice_item totals as the per-WO allocated amount.
    #
    # The COALESCE on `total` is defensive — older line items might have
    # used `total_price` only.
    op.execute("""
        INSERT INTO invoice_work_orders (
            invoice_id, work_order_id, allocated_amount,
            created_at, updated_at, is_active, version
        )
        SELECT
            ii.invoice_id,
            wl.work_order_id,
            COALESCE(SUM(COALESCE(ii.total, ii.total_price, 0)), 0) AS allocated_amount,
            NOW(), NOW(), TRUE, 1
        FROM invoice_items ii
        JOIN worklogs wl ON wl.id = ii.worklog_id
        WHERE ii.deleted_at IS NULL
          AND wl.work_order_id IS NOT NULL
        GROUP BY ii.invoice_id, wl.work_order_id
        ON CONFLICT (invoice_id, work_order_id) DO NOTHING
    """)


def downgrade():
    op.drop_table("invoice_work_orders")
