"""
WorklogSegment model - קטעי עבודה בדיווח
מקטע עבודה/הפסקה בדיווח שעות

פירוט שעות (לפי מפרט אישור דיווח):
| מקטע  | סוג   | שעות |
| עבודה | עבודה | 2:00 |
| הפסקה | מנוחה | 0:30 |
...
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import time, datetime, timedelta

from sqlalchemy import Integer, Time, ForeignKey, String, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.worklog import Worklog


class WorklogSegment(BaseModel):
    """
    WorklogSegment model - קטע עבודה/הפסקה

    פירוט שעות בדיווח:
    - segment_number: מספר סידורי
    - segment_type: 'work' או 'break'
    - start_time, end_time: זמני התחלה וסיום
    - work_minutes, break_minutes: דקות עבודה/הפסקה
    """

    __tablename__ = "worklog_segments"

    __table_args__ = {"extend_existing": True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    worklog_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("worklogs.id"), nullable=False, index=True)

    # Segment details
    segment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    segment_type: Mapped[Optional[str]] = mapped_column(
        String(20), default="work", nullable=True)  # 'work' or 'break'
    activity: Mapped[Optional[str]] = mapped_column(Unicode(200), nullable=True)  # תיאור פעילות

    # Timing
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    work_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    break_minutes: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)

    # Relationships
    worklog: Mapped["Worklog"] = relationship("Worklog")

    # Properties
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration: H:MM"""
        total_minutes = self.work_minutes + (self.break_minutes or 0)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}:{minutes:02d}"

    @property
    def work_hours_decimal(self) -> float:
        """Get work hours as decimal"""
        return self.work_minutes / 60.0

    @property
    def break_hours_decimal(self) -> float:
        """Get break hours as decimal"""
        return (self.break_minutes or 0) / 60.0

    def __repr__(self):
        return f"<WorklogSegment(id={self.id}, worklog_id={self.worklog_id}, type={self.segment_type}, segment={self.segment_number})>"
