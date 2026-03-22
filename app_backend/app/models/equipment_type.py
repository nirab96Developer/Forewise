"""
Equipment Type Model - סוגי ציוד
LOOKUP entity
"""

from __future__ import annotations

from typing import Optional
from decimal import Decimal
from datetime import datetime

from sqlalchemy import Integer, Unicode, Numeric, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class EquipmentType(Base):
    """
    Equipment Type model - סוג ציוד
    Table: equipment_types (12 columns)
    Category: LOOKUP
    """
    __tablename__ = "equipment_types"
    __table_args__ = {'implicit_returning': False}  # Has trigger

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic Information - Required
    code: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, unique=True, index=True,
        comment="קוד סוג ציוד"
    )
    
    name: Mapped[str] = mapped_column(
        Unicode(200), nullable=False, index=True,
        comment="שם סוג הציוד"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="תיאור"
    )
    
    category: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True,
        comment="קטגוריה"
    )

    # Rates - Required
    default_hourly_rate: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="תעריף שעתי ברירת מחדל"
    )
    
    default_daily_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="תעריף יומי ברירת מחדל"
    )
    
    default_storage_hourly_rate: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="תעריף אחסון שעתי"
    )

    # Display
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="סדר תצוגה"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default='1',
        comment="פעיל"
    )

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=False, server_default=func.now(),
        comment="תאריך יצירה"
    )
    
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, server_default=func.now(),
        comment="תאריך עדכון"
    )

    # Properties
    @property
    def display_name(self) -> str:
        return f"{self.code}: {self.name}" if self.code else self.name

    def __repr__(self):
        return f"<EquipmentType(id={self.id}, code='{self.code}', name='{self.name}')>"
