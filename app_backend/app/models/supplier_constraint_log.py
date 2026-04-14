"""
SupplierConstraintLog model - לוג אילוצי ספקים
Simple log table - no triggers, no version/deleted_at/is_active
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

if TYPE_CHECKING:
    pass


class SupplierConstraintLog(Base):
    """SupplierConstraintLog model - רישום אילוץ ספק
    
    Simple log table - no triggers, no version/deleted_at/is_active columns
    """
    __tablename__ = "supplier_constraint_logs"
    __table_args__ = {'extend_existing': True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    work_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("work_orders.id"), nullable=False)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False)
    constraint_reason_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("supplier_constraint_reasons.id"), nullable=True
    )

    # Details
    constraint_reason_text: Mapped[str] = mapped_column(String(500), nullable=False)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Created by
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamp
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True,
        server_default=text('SYSUTCDATETIME()')
    )

    # Approval
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self):
        return f"<SupplierConstraintLog(id={self.id}, work_order_id={self.work_order_id}, supplier_id={self.supplier_id})>"
