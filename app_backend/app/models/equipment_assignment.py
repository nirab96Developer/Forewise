"""
EquipmentAssignment model
TRANSACTIONS category
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.equipment import Equipment
    from app.models.project import Project


class EquipmentAssignment(BaseModel):
    """
    EquipmentAssignment model
    Category: TRANSACTIONS (has is_active, created_at, updated_at - no deleted_at, version)
    """
    __tablename__ = "equipment_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    equipment_id: Mapped[int] = mapped_column(Integer, ForeignKey('equipment.id'), nullable=False, index=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('projects.id'), nullable=True, index=True)
    assigned_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Dates
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Rates
    hourly_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    daily_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Hours
    planned_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Status
    status: Mapped[Optional[str]] = mapped_column(Unicode(20), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Unicode, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Unicode, nullable=True)
    
    # Relationships
    equipment: Mapped["Equipment"] = relationship("Equipment", foreign_keys=[equipment_id], lazy="joined")
    project: Mapped[Optional["Project"]] = relationship("Project", lazy="select")

    def __repr__(self):
        return f"<EquipmentAssignment(id={self.id}, equipment_id={self.equipment_id}, project_id={self.project_id})>"
