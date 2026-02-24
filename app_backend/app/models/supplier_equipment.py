"""
SupplierEquipment model - ציוד של ספקים
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import Optional
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, Boolean, DateTime, ForeignKey, Numeric, Unicode
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class SupplierEquipment(Base):
    """SupplierEquipment model - ציוד ספק - SYNCED WITH DB"""

    __tablename__ = "supplier_equipment"

    __table_args__ = {"extend_existing": True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys - DB: int, NO / int, NO
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False)
    equipment_category_id: Mapped[int] = mapped_column(Integer, ForeignKey("equipment_categories.id"), nullable=False)
    equipment_model_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("equipment_models.id"), nullable=True, index=True)

    # Quantity - DB: int, YES, default=1
    quantity_available: Mapped[Optional[int]] = mapped_column(Integer, default=1, nullable=True)

    # Rates - DB: decimal, YES
    hourly_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Status - DB: varchar + bit
    status: Mapped[Optional[str]] = mapped_column(Unicode(20), nullable=True, default="available")
    license_plate: Mapped[Optional[str]] = mapped_column(Unicode(50), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps - DB: timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<SupplierEquipment(id={self.id}, supplier_id={self.supplier_id}, model_id={self.equipment_model_id})>"

