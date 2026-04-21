"""
Invoice model - חשבוניות
CORE entity with full audit columns
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Integer, Numeric, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

if TYPE_CHECKING:
    pass


class Invoice(BaseModel):
    """
    Invoice model - חשבונית
    Table: invoices (21 columns)
    Category: CORE (has created_at, updated_at, deleted_at, is_active, version)

    Represents an invoice in the system.
    """
    __tablename__ = "invoices"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Business Identifier - UNIQUE!
    invoice_number: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, unique=True, index=True,
        comment="מספר חשבונית ייחודי"
    )

    # Foreign Keys
    supplier_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True,
        comment="ספק (no FK constraint in DB!)"
    )

    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True,
        comment="פרויקט (no FK constraint in DB!)"
    )

    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True,
        comment="נוצר על ידי (no FK constraint in DB!)"
    )

    # Dates
    issue_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True,
        comment="תאריך הנפקה"
    )

    due_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True,
        comment="תאריך פירעון"
    )

    # Financial Amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="סכום לפני מע\"מ"
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="סכום מע\"מ"
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="סכום כולל"
    )

    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=0,
        comment="סכום ששולם"
    )

    # Status & Payment
    status: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, index=True,
        comment="סטטוס: DRAFT, PENDING, APPROVED, PAID, CANCELLED"
    )

    payment_method: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True,
        comment="אמצעי תשלום"
    )

    payment_reference: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True,
        comment="אסמכתה / מספר עסקה"
    )

    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True,
        comment="תאריך התשלום בפועל"
    )

    paid_by: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True,
        comment="מי סימן כשולמה (no FK constraint in DB!)"
    )

    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="תאריך שליחה לספק"
    )

    # Additional
    notes: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="הערות"
    )

    pdf_path: Mapped[Optional[str]] = mapped_column(
        Unicode(500), nullable=True,
        comment="נתיב לקובץ PDF"
    )

    metadata_json: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="מטא-דאטה"
    )

    # Audit columns from BaseModel:
    # created_at, updated_at, deleted_at, is_active, version

    # Relationships - will be added after InvoiceItem and InvoicePayment are created
    # items: Mapped[List["InvoiceItem"]] = relationship(...)
    # payments: Mapped[List["InvoicePayment"]] = relationship(...)

    # Properties
    @property
    def display_name(self) -> str:
        """Display name for UI"""
        return f"Invoice {self.invoice_number}"

    @property
    def balance_due(self) -> Decimal:
        """Calculate remaining balance"""
        return self.total_amount - self.paid_amount

    @property
    def is_paid(self) -> bool:
        """Check if fully paid"""
        return self.paid_amount >= self.total_amount

    @property
    def is_overdue(self) -> bool:
        """Check if overdue"""
        from datetime import date as dt
        return self.due_date < dt.today() and not self.is_paid

    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', status='{self.status}')>"
