"""
InvoiceItem model - פריטי חשבונית
CORE entity
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Numeric, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.worklog import Worklog


class InvoiceItem(BaseModel):
    """
    InvoiceItem model - פריט חשבונית
    Table: invoice_items (21 columns)
    Category: CORE
    """
    __tablename__ = "invoice_items"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    invoice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('invoices.id'), nullable=False, index=True,
        comment="חשבונית"
    )
    
    worklog_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True,
        comment="דיווח עבודה (no FK in DB)"
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True,
        comment="מספר שורה"
    )

    description: Mapped[str] = mapped_column(
        Unicode(500), nullable=False,
        comment="תיאור"
    )

    item_code: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True,
        comment="קוד פריט"
    )

    # Quantities & Prices
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="כמות"
    )
    
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="מחיר יחידה"
    )

    # Discounts
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=0,
        comment="אחוז הנחה"
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=0,
        comment="סכום הנחה"
    )

    # Totals
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="סכום לפני מע\"מ"
    )

    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.17,
        comment="שיעור מע\"מ"
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="סכום מע\"מ"
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="סכום כולל"
    )

    # Legacy DB compatibility: old total column still required as NOT NULL.
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="סכום כולל (legacy)"
    )

    # Additional
    notes: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="הערות"
    )

    metadata_json: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="מטא-דאטה"
    )

    # Audit from BaseModel: created_at, updated_at, deleted_at, is_active, version

    # Relationship
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        lazy="select"
    )

    @property
    def display_name(self) -> str:
        return f"Line {self.line_number}: {self.description[:50]}"

    def __repr__(self):
        return f"<InvoiceItem(id={self.id}, invoice_id={self.invoice_id}, line={self.line_number})>"
