# app/models/activity_type.py
"""
Activity Type model - סוגי פעולות לדיווחי שעות
LOOKUP table - uses is_active instead of deleted_at
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Boolean, DateTime, Unicode, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ActivityType(Base):
    """Activity Type - סוגי פעולות לדיווחי שעות
    
    LOOKUP table - no deleted_at or version columns
    Uses is_active for soft delete behavior
    """
    
    __tablename__ = "activity_types"
    __table_args__ = {'implicit_returning': False, 'extend_existing': True}
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Business fields
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Unicode(500), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Status
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True, nullable=True)
    
    # Order
    sort_order: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    display_order: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    
    # Timestamps (DB has triggers for updated_at)
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
        return f"<ActivityType(id={self.id}, code='{self.code}', name='{self.name}')>"
