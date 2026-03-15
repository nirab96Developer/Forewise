"""
SupplierRotation model - רוטציה של ספקים
SYNCED WITH DB (kkl_forest_prod) - 11.02.2026
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import date, datetime

from sqlalchemy import Integer, String, Text, Boolean, Date, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.supplier import Supplier


class SupplierRotation(BaseModel):
    """SupplierRotation model - synced with actual DB columns"""

    __tablename__ = "supplier_rotations"

    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False)
    
    # Equipment classification
    equipment_type_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    equipment_category_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Geography
    region_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    area_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Rotation
    rotation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    rotation_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_assignments: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    successful_completions: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    rejection_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Dates
    last_assignment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Performance
    avg_response_time_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_completion_time_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Availability
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_available: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    unavailable_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    unavailable_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<SupplierRotation(id={self.id}, supplier_id={self.supplier_id}, position={self.rotation_position})>"
