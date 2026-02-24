"""
Supplier Constraint Reason Model - סיבות אילוץ ספקים
LOOKUP entity with multilingual support
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime

from sqlalchemy import Integer, Unicode, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class SupplierConstraintReason(Base):
    """
    Supplier Constraint Reason model - סיבת אילוץ ספק
    Table: supplier_constraint_reasons (16 columns)
    Category: LOOKUP (with soft delete)
    """
    __tablename__ = "supplier_constraint_reasons"
    __table_args__ = {'implicit_returning': False}  # Has trigger

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic Information - Multilingual
    code: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, unique=True, index=True,
        comment="קוד סיבה"
    )
    
    name_he: Mapped[str] = mapped_column(
        Unicode(200), nullable=False, index=True,
        comment="שם בעברית"
    )
    
    name_en: Mapped[Optional[str]] = mapped_column(
        Unicode(200), nullable=True,
        comment="שם באנגלית"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="תיאור"
    )
    
    category: Mapped[str] = mapped_column(
        Unicode(100), nullable=False, index=True,
        comment="קטגוריה"
    )

    # Flags
    requires_additional_text: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="האם דורש טקסט נוסף"
    )
    
    requires_approval: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="האם דורש אישור"
    )

    # Display & Usage
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="סדר תצוגה"
    )
    
    usage_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="מספר שימושים"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default='1',
        comment="פעיל"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(),
        comment="תאריך יצירה"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(),
        comment="תאריך עדכון"
    )
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="תאריך מחיקה"
    )

    # Version & Metadata
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        comment="גרסה"
    )
    
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="מטא-דאטא JSON"
    )

    # Properties
    @property
    def display_name(self) -> str:
        return self.name_he
    
    @property
    def name(self) -> str:
        """Alias for name_he"""
        return self.name_he

    def __repr__(self):
        return f"<SupplierConstraintReason(id={self.id}, code='{self.code}', name_he='{self.name_he}')>"
