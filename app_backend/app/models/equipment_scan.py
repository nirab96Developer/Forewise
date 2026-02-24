"""
EquipmentScan model - סריקות ציוד (QR/Barcode)
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.equipment import Equipment
    from app.models.location import Location
    from app.models.user import User


class EquipmentScan(BaseModel):
    """EquipmentScan model - סריקת ציוד - SYNCED WITH DB"""

    __tablename__ = "equipment_scans"

    __table_args__ = {'implicit_returning': False, 'extend_existing': True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys - DB: int, NO / int, NO / int, YES
    equipment_id: Mapped[int] = mapped_column(Integer, ForeignKey("equipment.id"), nullable=False)
    scanned_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    location_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("locations.id"), nullable=True)

    # Scan details - DB: nvarchar(20), NO / nvarchar(100), NO / datetime2, NO
    scan_type: Mapped[str] = mapped_column(String(20), nullable=False)
    scan_value: Mapped[str] = mapped_column(String(100), nullable=False)
    scan_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # GPS - DB: float, YES
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Device info - DB: nvarchar(-1), YES / nvarchar(50), YES
    device_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    purpose: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Status - DB: nvarchar(20), NO / bit, NO
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Notes - DB: nvarchar(500), YES
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Work Order association (for WORK_ORDER_ATTACH purpose)
    work_order_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("work_orders.id"), nullable=True)

    # Relationships
    # equipment: Mapped["Equipment"] = relationship("Equipment")
    # scanner: Mapped["User"] = relationship("User")
    # location: Mapped[Optional["Location"]] = relationship("Location")

    def __repr__(self):
        return f"<EquipmentScan(id={self.id}, equipment_id={self.equipment_id}, scan_type='{self.scan_type}')>"
