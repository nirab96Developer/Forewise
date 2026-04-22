"""create budget_commitments + backfill from existing freeze state

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-04-22

Phase 1.1 of the model-restructure roadmap.

Adds an explicit ledger row per (budget, work_order) money commitment so
freeze/release/spend stop being implicit mutations on `budgets.committed_amount`
that nobody can audit after the fact.

Backfill rule:
- For every active WorkOrder with `frozen_amount > 0` AND a budget that matches
  its project, create one row with `status='FROZEN'`, `frozen_amount=wo.frozen_amount`,
  `spent_amount=0`. This mirrors the current state 1:1 — `SUM(frozen_amount)` per
  budget equals the existing `budgets.committed_amount` afterwards.

The existing `budgets.committed_amount` / `budgets.spent_amount` and
`work_orders.frozen_amount` / `work_orders.remaining_frozen` columns are
**kept** for now. Phase 1.1 dual-writes; Phase 3 will drop the old fields.

Idempotent — safe to re-run (table create skipped if exists; backfill uses
INSERT...ON CONFLICT DO NOTHING semantics via NOT EXISTS guard).
"""

from alembic import op
import sqlalchemy as sa


revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Create the table if it doesn't already exist (defensive — alembic should
    # only run upgrade once, but a previous failed run can leave the table).
    if "budget_commitments" not in inspector.get_table_names():
        op.create_table(
            "budget_commitments",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("budget_id", sa.Integer,
                      sa.ForeignKey("budgets.id", ondelete="CASCADE"),
                      nullable=False, index=True),
            sa.Column("work_order_id", sa.Integer,
                      sa.ForeignKey("work_orders.id", ondelete="CASCADE"),
                      nullable=False, index=True),
            sa.Column("invoice_id", sa.Integer,
                      sa.ForeignKey("invoices.id", ondelete="SET NULL"),
                      nullable=True, index=True),
            sa.Column("frozen_amount", sa.Numeric(18, 2), nullable=False,
                      server_default=sa.text("0")),
            sa.Column("spent_amount", sa.Numeric(18, 2), nullable=False,
                      server_default=sa.text("0")),
            sa.Column("status", sa.Unicode(20), nullable=False,
                      server_default=sa.text("'FROZEN'")),
            sa.Column("frozen_at", sa.DateTime, nullable=False,
                      server_default=sa.text("NOW()")),
            sa.Column("spent_at", sa.DateTime, nullable=True),
            sa.Column("released_at", sa.DateTime, nullable=True),
            sa.Column("notes", sa.Unicode, nullable=True),
            sa.Column("metadata_json", sa.Unicode, nullable=True),
            # Audit (BaseModel fields)
            sa.Column("created_at", sa.DateTime, nullable=False,
                      server_default=sa.text("NOW()")),
            sa.Column("updated_at", sa.DateTime, nullable=False,
                      server_default=sa.text("NOW()")),
            sa.Column("deleted_at", sa.DateTime, nullable=True),
            sa.Column("is_active", sa.Boolean, nullable=False,
                      server_default=sa.text("TRUE")),
            sa.Column("version", sa.Integer, nullable=False,
                      server_default=sa.text("1")),
        )
        op.create_index(
            "ix_budget_commitments_budget_status",
            "budget_commitments", ["budget_id", "status"],
        )
        op.create_index(
            "ix_budget_commitments_wo_status",
            "budget_commitments", ["work_order_id", "status"],
        )

    # Backfill — only for live WOs that have a positive freeze and no
    # commitment row yet.
    op.execute("""
        INSERT INTO budget_commitments (
            budget_id, work_order_id, frozen_amount, spent_amount,
            status, frozen_at, created_at, updated_at, is_active, version
        )
        SELECT
            b.id,
            w.id,
            COALESCE(w.frozen_amount, 0),
            0,
            'FROZEN',
            COALESCE(w.created_at, NOW()),
            NOW(),
            NOW(),
            TRUE,
            1
        FROM work_orders w
        JOIN budgets b
          ON b.project_id = w.project_id
         AND b.deleted_at IS NULL
         AND b.is_active = TRUE
        WHERE w.deleted_at IS NULL
          AND COALESCE(w.frozen_amount, 0) > 0
          AND NOT EXISTS (
            SELECT 1 FROM budget_commitments c
            WHERE c.work_order_id = w.id AND c.status = 'FROZEN'
          )
    """)

    # Reconcile legacy aggregates on `budgets` to match the new ledger.
    # The audit found at least one row where committed_amount drifted
    # because cancelled/stopped WOs had leaked their freeze (the very bug
    # this restructure exists to fix). Snap the legacy field to truth.
    op.execute("""
        WITH agg AS (
            SELECT budget_id, COALESCE(SUM(frozen_amount), 0) AS committed
            FROM budget_commitments
            WHERE status = 'FROZEN' AND deleted_at IS NULL
            GROUP BY budget_id
        )
        UPDATE budgets b
        SET committed_amount = COALESCE(agg.committed, 0),
            remaining_amount = COALESCE(b.total_amount, 0)
                             - COALESCE(agg.committed, 0)
                             - COALESCE(b.spent_amount, 0),
            updated_at = NOW()
        FROM agg
        WHERE agg.budget_id = b.id
          AND ABS(COALESCE(b.committed_amount, 0)
                  - COALESCE(agg.committed, 0)) > 0.01;
    """)
    # Also zero-out committed_amount on budgets that have no live freezes
    # left (otherwise stale leftovers stay positive forever).
    op.execute("""
        UPDATE budgets b
        SET committed_amount = 0,
            remaining_amount = COALESCE(b.total_amount, 0)
                             - COALESCE(b.spent_amount, 0),
            updated_at = NOW()
        WHERE b.deleted_at IS NULL
          AND b.is_active = TRUE
          AND COALESCE(b.committed_amount, 0) > 0
          AND NOT EXISTS (
            SELECT 1 FROM budget_commitments c
            WHERE c.budget_id = b.id
              AND c.status = 'FROZEN'
              AND c.deleted_at IS NULL
          );
    """)


def downgrade():
    op.drop_index("ix_budget_commitments_wo_status",
                  table_name="budget_commitments")
    op.drop_index("ix_budget_commitments_budget_status",
                  table_name="budget_commitments")
    op.drop_table("budget_commitments")
