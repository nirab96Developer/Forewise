"""
EquipmentMaintenance model - תחזוקת ציוד
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Integer, String, Text, Boolean, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.equipment import Equipment
    from app.models.user import User


class EquipmentMaintenance(BaseModel):
    """EquipmentMaintenance model - תחזוקת ציוד - SYNCED WITH DB"""

    __tablename__ = "equipment_maintenance"

    __table_args__ = {'implicit_returning': False, 'extend_existing': True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys - DB: int, NO / int, YES
    equipment_id: Mapped[int] = mapped_column(Integer, ForeignKey("equipment.id"), nullable=False)
    performed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True)
    scheduled_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True)

    # Type - DB: nvarchar(50), NO
    maintenance_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Dates - DB: date, NO / date, YES / date, YES
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    performed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    next_maintenance_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Details - DB: nvarchar(-1), NO / YES
    description: Mapped[str] = mapped_column(Text, nullable=False)
    findings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actions_taken: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parts_replaced: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Time and cost - DB: decimal, YES
    hours_spent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    labor_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    parts_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    total_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Status - DB: nvarchar(20), NO / bit, NO
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Completion - DB: datetime2, YES
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    # equipment: Mapped["Equipment"] = relationship("Equipment")
    # performer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[performed_by])
    # scheduler: Mapped[Optional["User"]] = relationship("User", foreign_keys=[scheduled_by])

    def __repr__(self):
        return f"<EquipmentMaintenance(id={self.id}, equipment_id={self.equipment_id}, type='{self.maintenance_type}')>"
