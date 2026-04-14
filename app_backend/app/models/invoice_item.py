"""
InvoiceItem model - שורות חשבונית
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from decimal import Decimal

from sqlalchemy import Integer, String, Text, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

if TYPE_CHECKING:
    pass


class InvoiceItem(BaseModel):
    """InvoiceItem model - שורת חשבונית - SYNCED WITH DB"""

    __tablename__ = "invoice_items"

    __table_args__ = {"extend_existing": True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys - DB: int, NO / int, YES
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey("invoices.id"), nullable=False)
    worklog_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Line info
    line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    item_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Quantity and price - DB: decimal, NO
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Optional FK
    equipment_type_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Discount - DB: decimal, NO
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Totals - DB: decimal, NO
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Notes - DB: nvarchar(-1), YES
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # DB: bit, NO
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Relationships
    # invoice: Mapped["Invoice"] = relationship("Invoice")

    def __repr__(self):
        return f"<InvoiceItem(id={self.id}, invoice_id={self.invoice_id}, line={self.line_number})>"
