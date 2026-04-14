"""WorklogSegment model — פירוט שעות בדיווח"""
from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WorklogSegment(Base):
    __tablename__ = "worklog_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    worklog_id: Mapped[int] = mapped_column(Integer, ForeignKey("worklogs.id", ondelete="CASCADE"), nullable=False)
    segment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    activity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    payment_pct: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=100)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
