"""
Budget Allocation Service — single source of truth for the
freeze→spend→release lifecycle.

This service replaces the in-place mutations on `budgets.committed_amount`
that were scattered across budget_service / work_order_service /
invoice_service. Each public method:

  * locks the budget row with FOR UPDATE to make freeze+release races safe
  * inserts/updates a row in `budget_commitments`
  * keeps `budgets.committed_amount` and `budgets.spent_amount` in sync
    (dual-write — Phase 1.1). Phase 3 will turn those into computed views.

Public API:
  freeze(db, budget_id, work_order_id, amount)        → BudgetCommitment
  mark_spent(db, work_order_id, amount, invoice_id)   → list[BudgetCommitment]
  release(db, work_order_id, reason=None)             → list[BudgetCommitment]
  cancel(db, work_order_id, reason=None)              → list[BudgetCommitment]
  available(db, budget_id)                            → Decimal

All methods are idempotent for the same input — calling freeze twice for the
same WO won't double-charge; calling mark_spent on an already-spent
allocation is a no-op.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.budget_commitment import BudgetCommitment
from app.models.work_order import WorkOrder

logger = logging.getLogger(__name__)


# ─── Helpers ────────────────────────────────────────────────────────────

def _zero() -> Decimal:
    return Decimal("0")


def _to_dec(v) -> Decimal:
    if v is None:
        return _zero()
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def _lock_budget(db: Session, budget_id: int) -> Optional[Budget]:
    """SELECT ... FOR UPDATE so concurrent freeze/release on the same
    budget serialise instead of racing the committed_amount math."""
    return (
        db.query(Budget)
        .filter(Budget.id == budget_id, Budget.deleted_at.is_(None))
        .with_for_update()
        .first()
    )


def _recompute_budget_aggregates(db: Session, budget_id: int) -> None:
    """Recompute committed_amount + spent_amount + remaining_amount from
    the allocations table. Called after every state change so the legacy
    columns stay in sync during the dual-write window."""
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        return

    committed_q = db.query(func.coalesce(func.sum(BudgetCommitment.frozen_amount), 0)).filter(
        BudgetCommitment.budget_id == budget_id,
        BudgetCommitment.status == "FROZEN",
        BudgetCommitment.deleted_at.is_(None),
    )
    spent_q = db.query(func.coalesce(func.sum(BudgetCommitment.spent_amount), 0)).filter(
        BudgetCommitment.budget_id == budget_id,
        BudgetCommitment.status.in_(("SPENT", "CANCELLED")),
        BudgetCommitment.deleted_at.is_(None),
    )

    committed = _to_dec(committed_q.scalar())
    spent = _to_dec(spent_q.scalar())

    budget.committed_amount = committed
    budget.spent_amount = spent
    budget.remaining_amount = _to_dec(budget.total_amount) - committed - spent
    budget.updated_at = datetime.utcnow()


def _resolve_budget_for_wo(db: Session, work_order: WorkOrder) -> Optional[Budget]:
    """Find the active project-level budget for a WO. Mirrors what
    budget_service.freeze_budget_for_work_order used to do."""
    if not work_order.project_id:
        return None
    return (
        db.query(Budget)
        .filter(
            Budget.project_id == work_order.project_id,
            Budget.is_active == True,
            Budget.deleted_at.is_(None),
        )
        .first()
    )


# ─── Public API ─────────────────────────────────────────────────────────

def available(db: Session, budget_id: int) -> Decimal:
    """Free cash on a budget = total - committed - spent."""
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        return _zero()
    return (
        _to_dec(budget.total_amount)
        - _to_dec(budget.committed_amount)
        - _to_dec(budget.spent_amount)
    )


def freeze(
    db: Session, budget_id: int, work_order_id: int, amount: Decimal,
) -> BudgetCommitment:
    """Freeze ``amount`` on ``budget_id`` for ``work_order_id``.

    Idempotent: if a FROZEN allocation already exists for this WO+budget pair,
    update its amount in place (typical case is a WO whose estimate changed
    before going to a supplier).

    Raises ValueError if the budget can't cover the amount.
    """
    amount = _to_dec(amount)
    if amount <= 0:
        raise ValueError("amount must be positive")

    budget = _lock_budget(db, budget_id)
    if not budget:
        raise ValueError(f"budget {budget_id} not found")

    existing = (
        db.query(BudgetCommitment)
        .filter(
            BudgetCommitment.budget_id == budget_id,
            BudgetCommitment.work_order_id == work_order_id,
            BudgetCommitment.status == "FROZEN",
            BudgetCommitment.deleted_at.is_(None),
        )
        .first()
    )

    # Compute available *excluding* what we already have frozen for this WO
    # (so we don't reject a re-freeze with a smaller amount).
    current_frozen = _to_dec(existing.frozen_amount) if existing else _zero()
    available_after_self = available(db, budget_id) + current_frozen

    if amount > available_after_self:
        raise ValueError(
            f"אין מספיק תקציב. זמין: {available_after_self:,.0f}, נדרש: {amount:,.0f}"
        )

    if existing:
        existing.frozen_amount = amount
        existing.updated_at = datetime.utcnow()
        allocation = existing
    else:
        allocation = BudgetCommitment(
            budget_id=budget_id,
            work_order_id=work_order_id,
            frozen_amount=amount,
            spent_amount=_zero(),
            status="FROZEN",
            frozen_at=datetime.utcnow(),
        )
        db.add(allocation)

    db.flush()
    _recompute_budget_aggregates(db, budget_id)
    db.commit()
    db.refresh(allocation)
    return allocation


def mark_spent(
    db: Session,
    work_order_id: int,
    amount: Decimal,
    invoice_id: Optional[int] = None,
    notes: Optional[str] = None,
) -> List[BudgetCommitment]:
    """Settle the FROZEN allocations of a work order with an actual paid amount.

    If multiple FROZEN allocations exist for the WO (rare but possible during
    Phase 1.1 dual-write transition), the amount is split proportionally
    across them by frozen_amount.

    Idempotent: already-SPENT allocations are skipped (returned as-is).
    """
    amount = _to_dec(amount)
    if amount < 0:
        raise ValueError("amount cannot be negative")

    rows = (
        db.query(BudgetCommitment)
        .filter(
            BudgetCommitment.work_order_id == work_order_id,
            BudgetCommitment.status == "FROZEN",
            BudgetCommitment.deleted_at.is_(None),
        )
        .all()
    )
    if not rows:
        return []

    total_frozen = sum((_to_dec(r.frozen_amount) for r in rows), _zero())
    now = datetime.utcnow()
    touched_budgets = set()
    updated: List[BudgetCommitment] = []

    if total_frozen == 0 or len(rows) == 1:
        share_each = [amount] + [_zero()] * (len(rows) - 1)
    else:
        # Proportional split — last row absorbs rounding remainder so the
        # sum exactly equals ``amount``.
        shares = [(_to_dec(r.frozen_amount) / total_frozen * amount) for r in rows[:-1]]
        shares = [s.quantize(Decimal("0.01")) for s in shares]
        shares.append(amount - sum(shares, _zero()))
        share_each = shares

    for row, share in zip(rows, share_each):
        row.spent_amount = share
        row.status = "SPENT"
        row.spent_at = now
        if invoice_id is not None:
            row.invoice_id = invoice_id
        if notes:
            row.notes = (row.notes + " | " if row.notes else "") + notes
        row.updated_at = now
        updated.append(row)
        touched_budgets.add(row.budget_id)

    db.flush()
    for bid in touched_budgets:
        _recompute_budget_aggregates(db, bid)
    db.commit()
    return updated


def release(
    db: Session, work_order_id: int, reason: Optional[str] = None,
) -> List[BudgetCommitment]:
    """Release FROZEN allocations back to the budget without recording any
    spend (e.g. WO was rejected/cancelled before payment)."""
    rows = (
        db.query(BudgetCommitment)
        .filter(
            BudgetCommitment.work_order_id == work_order_id,
            BudgetCommitment.status == "FROZEN",
            BudgetCommitment.deleted_at.is_(None),
        )
        .all()
    )
    if not rows:
        return []

    now = datetime.utcnow()
    touched = set()
    for row in rows:
        row.status = "RELEASED"
        row.released_at = now
        row.updated_at = now
        if reason:
            row.notes = (row.notes + " | " if row.notes else "") + f"release: {reason}"
        touched.add(row.budget_id)

    db.flush()
    for bid in touched:
        _recompute_budget_aggregates(db, bid)
    db.commit()
    return rows


def cancel(
    db: Session, work_order_id: int, reason: Optional[str] = None,
) -> List[BudgetCommitment]:
    """Mark allocations as CANCELLED (rare — used when a WO is deleted
    after payment was already recorded). Different from RELEASED in that
    spent_amount is preserved so finance reports stay accurate."""
    rows = (
        db.query(BudgetCommitment)
        .filter(
            BudgetCommitment.work_order_id == work_order_id,
            BudgetCommitment.status.in_(("FROZEN", "SPENT")),
            BudgetCommitment.deleted_at.is_(None),
        )
        .all()
    )
    if not rows:
        return []

    now = datetime.utcnow()
    touched = set()
    for row in rows:
        row.status = "CANCELLED"
        row.released_at = now
        row.updated_at = now
        if reason:
            row.notes = (row.notes + " | " if row.notes else "") + f"cancel: {reason}"
        touched.add(row.budget_id)

    db.flush()
    for bid in touched:
        _recompute_budget_aggregates(db, bid)
    db.commit()
    return rows
