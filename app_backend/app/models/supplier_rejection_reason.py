"""
SupplierRejectionReason model - סיבות לדחיית ספק
LOOKUP table - uses is_active instead of deleted_at
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Boolean, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SupplierRejectionReason(Base):
    """SupplierRejectionReason model - סיבה לדחיית ספק
    
    LOOKUP table - no deleted_at or version columns
    Uses is_active for soft delete behavior
    """
    __tablename__ = "supplier_rejection_reasons"
    __table_args__ = {'implicit_returning': False, 'extend_existing': True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Business fields
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Category
    category: Mapped[Optional[str]] = mapped_column(String(50), default="OPERATIONAL", nullable=True)

    # Flags
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True, nullable=True)
    requires_additional_text: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    requires_approval: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)

    # Order and usage
    display_order: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    usage_count: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True,
        server_default=text('SYSUTCDATETIME()')
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True,
        server_default=text('SYSUTCDATETIME()')
    )

    def __repr__(self):
        return f"<SupplierRejectionReason(id={self.id}, code='{self.code}', name='{self.name}')>"
