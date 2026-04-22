"""lock down status columns with CHECK constraints (Phase 2.1)

Revision ID: a8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-04-22

Phase 2.1 of the model-restructure roadmap.

Goal
----
Stop accepting arbitrary strings into status columns. After Phase 0 we found
budgets.status held both 'active' and 'ACTIVE'; in earlier audits the same
problem hit work_orders.status (lowercase 'completed' alongside 'COMPLETED').
Once a bad value lands in a status column every dashboard filter, every
state-machine guard, and every export starts behaving inconsistently.

Decision: CHECK constraints, not PostgreSQL ENUM types
------------------------------------------------------
Both achieve the same write-time enforcement. CHECK constraints win because:
  * Adding/removing a status is a simple `ALTER TABLE` (single-statement,
    near-instant) — PG ENUM types require recreating the type and every
    column that depends on it.
  * SQLAlchemy models keep their `Unicode(50)` declaration. No code change
    on the model side; the constraint runs purely at the database layer.
  * Same downstream effect for the FE strings dictionary (each canonical
    value still maps 1:1 to a Hebrew label via src/strings/statuses.ts).

Scope of this migration
-----------------------
Only the columns whose write paths are 100% clean (audited 2026-04-22, all
writes use UPPERCASE canonical values):

  * work_orders.status        (11 values)
  * worklogs.status           (7 values)
  * invoices.status           (9 values)
  * budgets.status            (6 values)  [normalised by c4d5e6f7a8b9]
  * budget_commitments.status (4 values)  [new in Phase 1.1]

Deliberately NOT in this migration:
  * users.status               — DB still has both 'ACTIVE' and 'active'
  * projects.status            — lowercase 'active'/'inactive' currently
  * equipment.status           — lowercase 'active'/'available' currently

These three need a data normalisation pass first; their FE strings keys are
already UPPERCASE but the BE write paths are split across many old call
sites. Will be tackled in a follow-up Phase 2.1b once we audit those writes.
"""

from alembic import op
from sqlalchemy import text


revision = "a8b9c0d1e2f3"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


# Canonical status values per table. KEEP IN SYNC with src/strings/statuses.ts
# on the FE side. Adding a new value = one entry in both files.
WORK_ORDER_STATUSES = (
    "PENDING",
    "DISTRIBUTING",
    "SUPPLIER_ACCEPTED_PENDING_COORDINATOR",
    "APPROVED_AND_SENT",
    "IN_PROGRESS",
    "NEEDS_RE_COORDINATION",
    "COMPLETED",
    "REJECTED",
    "CANCELLED",
    "EXPIRED",
    "STOPPED",
)

WORKLOG_STATUSES = (
    "DRAFT",
    "PENDING",
    "SUBMITTED",
    "APPROVED",
    "REJECTED",
    "INVOICED",
    "CANCELLED",
)

INVOICE_STATUSES = (
    "DRAFT",
    "PENDING",
    "APPROVED",
    "SENT",
    "PAID",
    "OVERDUE",
    "CANCELLED",
    "VOID",
    "REJECTED",
)

BUDGET_STATUSES = (
    "DRAFT",
    "ACTIVE",
    "FROZEN",
    "CLOSED",
    "EXHAUSTED",
    "ARCHIVED",
)

BUDGET_COMMITMENT_STATUSES = (
    "FROZEN",
    "SPENT",
    "RELEASED",
    "CANCELLED",
)


def _quote(values):
    return ", ".join(f"'{v}'" for v in values)


def _add_check(table: str, constraint: str, column: str, values: tuple):
    """Drop-and-recreate the CHECK constraint so the migration is idempotent."""
    op.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint}')
    op.execute(
        f'ALTER TABLE {table} '
        f'ADD CONSTRAINT {constraint} '
        f'CHECK ({column} IN ({_quote(values)}))'
    )


def _drop_check(table: str, constraint: str):
    op.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint}')


def upgrade():
    # Defensive sanity-pass: refuse to add the CHECK if any current row would
    # violate it. We do this by counting rows that don't match the canonical
    # set — if > 0, raise so the migration fails loudly instead of silently
    # rejecting future writes for data that the DB itself accepts today.
    for table, column, values in [
        ("work_orders",        "status", WORK_ORDER_STATUSES),
        ("worklogs",           "status", WORKLOG_STATUSES),
        ("invoices",           "status", INVOICE_STATUSES),
        ("budgets",            "status", BUDGET_STATUSES),
        ("budget_commitments", "status", BUDGET_COMMITMENT_STATUSES),
    ]:
        bind = op.get_bind()
        bad = bind.execute(text(
            f'SELECT COUNT(*) FROM {table} '
            f'WHERE {column} IS NOT NULL AND {column} NOT IN ({_quote(values)})'
        )).scalar()
        if bad and bad > 0:
            raise RuntimeError(
                f"Refusing to add CHECK on {table}.{column}: {bad} existing "
                f"rows hold a non-canonical value. Normalise the data first."
            )

    _add_check("work_orders",        "ck_work_orders_status",        "status", WORK_ORDER_STATUSES)
    _add_check("worklogs",           "ck_worklogs_status",           "status", WORKLOG_STATUSES)
    _add_check("invoices",           "ck_invoices_status",           "status", INVOICE_STATUSES)
    _add_check("budgets",            "ck_budgets_status",            "status", BUDGET_STATUSES)
    _add_check("budget_commitments", "ck_budget_commitments_status", "status", BUDGET_COMMITMENT_STATUSES)


def downgrade():
    _drop_check("work_orders",        "ck_work_orders_status")
    _drop_check("worklogs",           "ck_worklogs_status")
    _drop_check("invoices",           "ck_invoices_status")
    _drop_check("budgets",            "ck_budgets_status")
    _drop_check("budget_commitments", "ck_budget_commitments_status")
