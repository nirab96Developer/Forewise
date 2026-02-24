"""
WorkOrderStatus model - סטטוסי הזמנות עבודה
LOOKUP table - uses is_active instead of deleted_at
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Unicode, Boolean, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WorkOrderStatus(Base):
    """WorkOrderStatus model - סטטוס הזמנת עבודה
    
    LOOKUP table - no deleted_at or version columns
    Uses is_active for soft delete behavior
    """
    __tablename__ = "work_order_statuses"
    __table_args__ = {'implicit_returning': False, 'extend_existing': True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Business fields
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Unicode(500), nullable=True)

    # Status
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True, nullable=True)
    
    # Order
    display_order: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)

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
        return f"<WorkOrderStatus(id={self.id}, code='{self.code}', name='{self.name}')>"
