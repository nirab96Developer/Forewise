"""
EquipmentModel model - דגם כלי
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime

from sqlalchemy import Integer, Unicode, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import BaseModel


class EquipmentModel(BaseModel):
    """Equipment model master data."""

    __tablename__ = "equipment_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(
        Unicode(200), nullable=False, unique=True, index=True,
        comment="שם דגם כלי"
    )

    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("equipment_categories.id"), nullable=True, index=True,
        comment="קטגוריית ציוד"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default='1',
        comment="פעיל"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(),
        comment="תאריך יצירה"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(),
        comment="תאריך עדכון"
    )

    def __repr__(self):
        return f"<EquipmentModel(id={self.id}, name='{self.name}')>"
