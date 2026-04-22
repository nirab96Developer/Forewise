"""
Budget Commitment — explicit money-commitment ledger per work order.

NOTE: Named ``budget_commitments`` (not ``budget_allocations``) because an
unrelated allocation system already owns the latter table for the
region/area/department hierarchy. A "commitment" is the standard
finance term for funds that are earmarked but not yet spent — exactly what
this table represents.

State machine:

    FROZEN ──(invoice paid)──→ SPENT
       │
       └──(WO cancelled before pay)──→ RELEASED
       │
       └──(WO deleted after pay, rare)──→ CANCELLED

Aggregates on `budgets.committed_amount` / `spent_amount` should be derived
from this table, not maintained in parallel. (Dual-write transition is in
Phase 1.1; full cutover in Phase 3.)
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Unicode, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.budget import Budget
    from app.models.work_order import WorkOrder
    from app.models.invoice import Invoice


COMMITMENT_STATES = ("FROZEN", "SPENT", "RELEASED", "CANCELLED")


class BudgetCommitment(BaseModel):
    __tablename__ = "budget_commitments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    budget_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("budgets.id", ondelete="CASCADE"),
        nullable=False, index=True,
        comment="התקציב שממנו הוקצה הסכום",
    )

    work_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("work_orders.id", ondelete="CASCADE"),
        nullable=False, index=True,
        comment="הזמנת העבודה שמנצלת את ההקצאה",
    )

    invoice_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True, index=True,
        comment="החשבונית ששילמה (אחרי Phase 1.2)",
    )

    frozen_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0"),
        comment="הסכום שהוקפא בעת יצירת ההזמנה",
    )

    spent_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0"),
        comment="הסכום ששולם בפועל",
    )

    status: Mapped[str] = mapped_column(
        Unicode(20), nullable=False, default="FROZEN",
        comment="FROZEN | SPENT | RELEASED | CANCELLED",
    )

    frozen_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow,
        comment="מתי הוקפא",
    )

    spent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="מתי הסכום סומן כשולם",
    )

    released_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="מתי שוחרר/בוטל",
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="הערות חופשיות (סיבת ביטול וכד')",
    )

    metadata_json: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="מטא-דאטה",
    )

    # Audit columns inherited from BaseModel:
    # created_at, updated_at, deleted_at, is_active, version

    budget: Mapped["Budget"] = relationship(
        "Budget", foreign_keys=[budget_id], lazy="select"
    )

    work_order: Mapped["WorkOrder"] = relationship(
        "WorkOrder", foreign_keys=[work_order_id], lazy="select"
    )

    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice", foreign_keys=[invoice_id], lazy="select"
    )

    __table_args__ = (
        Index("ix_budget_commitments_budget_status", "budget_id", "status"),
        Index("ix_budget_commitments_wo_status", "work_order_id", "status"),
    )

    def __repr__(self):
        return (
            f"<BudgetCommitment id={self.id} budget={self.budget_id} "
            f"wo={self.work_order_id} status={self.status} "
            f"frozen={self.frozen_amount} spent={self.spent_amount}>"
        )
