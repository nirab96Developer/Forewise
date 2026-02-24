"""
WorklogStatus model - סטטוסי דיווחי עבודה
LOOKUP table - uses is_active instead of deleted_at
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Boolean, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WorklogStatus(Base):
    """WorklogStatus model - סטטוס דיווח עבודה
    
    LOOKUP table - no deleted_at or version columns
    Uses is_active for soft delete behavior
    """
    __tablename__ = "worklog_statuses"
    __table_args__ = {'implicit_returning': False, 'extend_existing': True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Business fields
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)

    # Status (NOT NULL in this table)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Order (NOT NULL in this table)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False,
        server_default=text('SYSUTCDATETIME()')
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True,
        server_default=text('SYSUTCDATETIME()')
    )

    def __repr__(self):
        return f"<WorklogStatus(id={self.id}, code='{self.code}', name='{self.name}')>"
