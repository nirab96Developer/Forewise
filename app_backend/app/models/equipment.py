"""
Equipment model - ציוד
CORE entity with full audit columns
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Unicode, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.equipment_type import EquipmentType


class Equipment(BaseModel):
    """
    Equipment model - ציוד
    Table: equipment
    Category: CORE (has deleted_at, is_active, version)

    Represents physical equipment/machinery in the system.
    Can be assigned to projects, locations, or users.
    """
    __tablename__ = "equipment"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic Information
    name: Mapped[str] = mapped_column(
        Unicode(255), nullable=False, index=True,
        comment="שם הציוד"
    )

    code: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True, unique=True, index=True,
        comment="קוד ציוד ייחודי"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="תיאור הציוד"
    )

    # Equipment Details
    equipment_type: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True,
        comment="סוג ציוד (legacy - use type_id)"
    )

    manufacturer: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True,
        comment="יצרן"
    )

    model: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True,
        comment="דגם"
    )

    license_plate: Mapped[Optional[str]] = mapped_column(
        Unicode(20), nullable=True, unique=True, index=True,
        comment="מספר רישוי (רכב)"
    )

    qr_code: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True, unique=True, index=True,
        comment="קוד QR"
    )

    fuel_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="סוג דלק (רכב)"
    )

    # Status
    status: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True, default='available', index=True,
        comment="סטטוס: available, in_use, maintenance, retired"
    )

    # Foreign Keys - Organization
    type_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('equipment_types.id'), nullable=True, index=True,
        comment="סוג ציוד (FK)"
    )

    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True,
        comment="קטגוריית ציוד (אין FK בפועל בDB!)"
    )

    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True,
        comment="ספק (אין FK בפועל בDB!)"
    )

    location_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True,
        comment="מיקום נוכחי (אין FK בפועל בDB!)"
    )

    assigned_to_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True,
        comment="משויך למשתמש (אין FK בפועל בDB!)"
    )

    assigned_project_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True,
        comment="משויך לפרויקט (אין FK בפועל בDB!)"
    )

    # Financial
    purchase_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        comment="תאריך רכישה"
    )

    purchase_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="מחיר רכישה"
    )

    hourly_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="תעריף שעתי"
    )

    daily_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="תעריף יומי"
    )

    storage_hourly_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="תעריף אחסון שעתי"
    )

    overnight_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True,
        comment="תעריף לינת שטח לכלי ספציפי"
    )

    night_guard: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, default=False,
        comment="הכלי מתאים לשמירת לילה"
    )

    # Maintenance
    last_maintenance: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        comment="תחזוקה אחרונה"
    )

    next_maintenance: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        comment="תחזוקה הבאה"
    )

    # Metadata
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="מטא-דאטה נוסף (JSON)"
    )

    # Relationships (only where FK exists in DB!)
    equipment_type_obj: Mapped[Optional["EquipmentType"]] = relationship(
        "EquipmentType",
        foreign_keys=[type_id],
        lazy="joined"
    )

    # Note: category_id, supplier_id, location_id, assigned_to_user_id, assigned_project_id
    # DO NOT have FK constraints in DB, so relationships handled in service layer if needed

    # Reverse relationships
    # Temporarily commented out to avoid circular import issues
    # Will be added after all related models are properly defined
    # assignments: Mapped[List["EquipmentAssignment"]] = relationship(...)
    # maintenance_records: Mapped[List["EquipmentMaintenance"]] = relationship(...)
    # scans: Mapped[List["EquipmentScan"]] = relationship(...)

    # Properties
    @property
    def is_available(self) -> bool:
        """Check if equipment is available"""
        return self.status == 'available' and self.is_active and not self.is_deleted

    @property
    def is_in_use(self) -> bool:
        """Check if equipment is currently in use"""
        return self.status == 'in_use'

    @property
    def needs_maintenance(self) -> bool:
        """Check if maintenance is due"""
        if not self.next_maintenance:
            return False
        return date.today() >= self.next_maintenance

    @property
    def display_name(self) -> str:
        """Get display name for equipment"""
        parts = [self.name]
        if self.license_plate:
            parts.append(f"({self.license_plate})")
        elif self.code:
            parts.append(f"[{self.code}]")
        return " ".join(parts)

    def __repr__(self):
        return f"<Equipment(id={self.id}, name='{self.name}', status='{self.status}')>"
