# app/schemas/calendar.py
"""Calendar schemas for holidays and events."""
from datetime import date, time
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types for calendar."""

    HOLIDAY = "holiday"
    WORK_ORDER = "work_order"
    WORKLOG = "worklog"
    PROJECT_DEADLINE = "project_deadline"
    MAINTENANCE = "maintenance"
    MEETING = "meeting"


class HolidayResponse(BaseModel):
    """Jewish holiday response."""

    date: date
    name_he: str
    name_en: Optional[str] = None
    is_workday: bool = False
    type: str = "major"  # major/minor/fast


class CalendarEventResponse(BaseModel):
    """Calendar event response."""

    id: Optional[int] = None
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    type: EventType
    title: str
    description: Optional[str] = None
    color: str = "#3B82F6"  # Default blue
    is_all_day: bool = False
    details: Optional[Dict[str, Any]] = None


class CalendarDayResponse(BaseModel):
    """Single day with all events."""

    date: date
    is_workday: bool = True
    is_holiday: bool = False
    holiday_name: Optional[str] = None
    events: List[CalendarEventResponse] = Field(default_factory=list)
    total_work_hours: float = 0


class CalendarMonthResponse(BaseModel):
    """Full month calendar response."""

    year: int
    month: int
    days: List[CalendarDayResponse]
    holidays: List[HolidayResponse]
    summary: Dict[str, Any] = Field(default_factory=dict)
