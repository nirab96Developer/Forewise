"""
Invoice ↔ Work Order link table.

Invoices in this system are batch documents — `generate_monthly_invoice`
rolls up every approved worklog of one supplier on one project for one
month, which can span multiple work orders. The old indirect path
(invoice → invoice_items.worklog_id → worklogs.work_order_id) needed three
joins to answer the simple question "which WOs does this invoice pay
for?", and made it impossible to record per-WO share without re-parsing
line items every time.

This explicit link table caches the relationship plus the per-WO money
share, so:
  * mark-paid can split the payment across budget commitments accurately
  * dashboards can show "invoices for WO X" with one join
  * deleting a WO can cascade the link without touching the invoice itself
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.work_order import WorkOrder


class InvoiceWorkOrder(BaseModel):
    __tablename__ = "invoice_work_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    invoice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False, index=True,
        comment="חשבונית אב",
    )

    work_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("work_orders.id", ondelete="CASCADE"),
        nullable=False, index=True,
        comment="הזמנת עבודה שמכוסה ע\"י החשבונית",
    )

    allocated_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0"),
        comment="הסכום שיוחס ל-WO זו מתוך סך החשבונית (כולל מע\"מ)",
    )

    # Audit columns from BaseModel:
    # created_at, updated_at, deleted_at, is_active, version

    invoice: Mapped["Invoice"] = relationship(
        "Invoice", foreign_keys=[invoice_id], lazy="select"
    )

    work_order: Mapped["WorkOrder"] = relationship(
        "WorkOrder", foreign_keys=[work_order_id], lazy="select"
    )

    __table_args__ = (
        UniqueConstraint("invoice_id", "work_order_id", name="uq_invoice_wo"),
    )

    def __repr__(self):
        return (
            f"<InvoiceWorkOrder invoice={self.invoice_id} "
            f"wo={self.work_order_id} amount={self.allocated_amount}>"
        )
