"""
Equipment Category Model - קטגוריות ציוד
CORE entity with self-referential hierarchy
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import Integer, Unicode, Boolean, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    pass


class EquipmentCategory(Base):
    """
    Equipment Category model - קטגוריית ציוד
    Table: equipment_categories (18 columns)
    Category: CORE (with soft delete)
    """
    __tablename__ = "equipment_categories"
    __table_args__ = {'implicit_returning': False}  # Has trigger

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic Information - Both UNIQUE
    name: Mapped[str] = mapped_column(
        Unicode(200), nullable=False, unique=True, index=True,
        comment="שם הקטגוריה"
    )
    
    code: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, unique=True, index=True,
        comment="קוד קטגוריה"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="תיאור"
    )

    # Self-referential hierarchy
    parent_category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('equipment_categories.id'), nullable=True, index=True,
        comment="קטגוריית אב"
    )

    # License & Certification
    requires_license: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="דורש רישיון"
    )
    
    license_type: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True,
        comment="סוג רישיון"
    )
    
    requires_certification: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="דורש הסמכה"
    )

    # Default Rates
    default_hourly_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="תעריף שעתי ברירת מחדל"
    )
    
    default_daily_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="תעריף יומי ברירת מחדל"
    )

    # Maintenance
    maintenance_interval_hours: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="מרווח תחזוקה בשעות"
    )
    
    maintenance_interval_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="מרווח תחזוקה בימים"
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

    # Self-referential relationship
    parent: Mapped[Optional["EquipmentCategory"]] = relationship(
        "EquipmentCategory",
        foreign_keys=[parent_category_id],
        remote_side=[id],
        lazy="select"
    )

    # Properties
    @property
    def display_name(self) -> str:
        return f"{self.code}: {self.name}" if self.code else self.name

    def __repr__(self):
        return f"<EquipmentCategory(id={self.id}, code='{self.code}', name='{self.name}')>"
