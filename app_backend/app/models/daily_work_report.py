"""
DailyWorkReport model - דוחות עבודה יומיים
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import date, datetime

from sqlalchemy import Integer, String, Text, Boolean, Date, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

if TYPE_CHECKING:
    pass


class DailyWorkReport(BaseModel):
    """DailyWorkReport model - דוח עבודה יומי - SYNCED WITH DB"""

    __tablename__ = "daily_work_reports"

    __table_args__ = {"extend_existing": True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys - DB: int, NO / int, YES
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    submitted_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Report date - DB: date, NO
    report_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Conditions - DB: nvarchar(100), YES / int, YES
    weather_conditions: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    workers_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Activities - DB: nvarchar(-1), YES
    activities_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    equipment_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    materials_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issues_reported: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Hours - DB: float, YES
    total_work_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_equipment_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Safety - DB: int, YES
    safety_incidents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status - DB: nvarchar(20), NO / bit, NO
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Timestamps - DB: datetime2, YES
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    # project: Mapped["Project"] = relationship("Project")
    # submitter: Mapped[Optional["User"]] = relationship("User", foreign_keys=[submitted_by])
    # approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<DailyWorkReport(id={self.id}, project_id={self.project_id}, date={self.report_date})>"
