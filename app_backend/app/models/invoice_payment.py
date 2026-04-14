"""
InvoicePayment model - תשלומים לחשבוניות
TRANSACTIONS category (is_active, created_at, updated_at - NO deleted_at/version per migration)
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, Unicode, Boolean, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class InvoicePayment(Base):
    """
    InvoicePayment model - תשלום לחשבונית
    Table: invoice_payments (17 columns)
    Category: TRANSACTIONS (NOT inheriting BaseModel - custom audit)
    
    Note: According to migration_decisions.json, invoice_payments is TRANSACTIONS
    but the actual DB has deleted_at and version! Using them.
    """
    __tablename__ = "invoice_payments"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    invoice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('invoices.id'), nullable=False, index=True,
        comment="חשבונית"
    )
    
    processed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=True, index=True,
        comment="עובד על ידי"
    )

    # Payment Details
    payment_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True,
        comment="תאריך תשלום"
    )
    
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="סכום"
    )
    
    payment_method: Mapped[str] = mapped_column(
        Unicode(50), nullable=False,
        comment="אמצעי תשלום"
    )

    # Reference Information
    reference_number: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True, index=True,
        comment="מספר אסמכתא"
    )
    
    transaction_id: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True,
        comment="מזהה עסקה"
    )
    
    bank_name: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True,
        comment="שם בנק"
    )
    
    account_number: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True,
        comment="מספר חשבון"
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

    # Audit - TRANSACTIONS category but DB has all columns
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text('NOW()'),
        comment="נוצר ב"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text('NOW()'),
        comment="עודכן ב"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="פעיל"
    )
    
    # DB actually has these even though category is TRANSACTIONS
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="נמחק ב"
    )
    
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        comment="גרסה"
    )

    # Relationship
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        lazy="select"
    )

    def __repr__(self):
        return f"<InvoicePayment(id={self.id}, invoice_id={self.invoice_id}, amount={self.amount})>"
