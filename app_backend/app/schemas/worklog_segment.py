# /root/app_backend/app/schemas/worklog_segment.py - חדש
"""Worklog segment schemas - Aligned with database model."""
from datetime import datetime, time
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SegmentType(str, Enum):
    """Segment type - matches model."""

    WORK = "work"
    BREAK = "break"


class WorklogSegmentBase(BaseModel):
    """Base worklog segment schema."""

    worklog_id: int = Field(..., gt=0, description="Worklog ID")

    # Segment details
    segment_order: int = Field(..., ge=1, le=10, description="Segment order")
    type: SegmentType = Field(..., description="Segment type")

    # Time
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    duration_hours: Decimal = Field(..., ge=0, le=24, description="Duration in hours")

    # Activity
    activity_type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    notes: Optional[str] = None

    # Flag
    is_standard: bool = Field(True, description="Is standard segment")


class WorklogSegmentCreate(WorklogSegmentBase):
    """Create worklog segment schema."""

    pass


class WorklogSegmentUpdate(BaseModel):
    """Update worklog segment schema."""

    segment_order: Optional[int] = Field(None, ge=1, le=10)
    type: Optional[SegmentType] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_hours: Optional[Decimal] = Field(None, ge=0, le=24)
    activity_type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    notes: Optional[str] = None
    is_standard: Optional[bool] = None
    is_active: Optional[bool] = None


class WorklogSegmentResponse(WorklogSegmentBase):
    """Worklog segment response schema."""

    id: int

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed
    is_work_segment: bool = False
    is_break_segment: bool = False
    duration_minutes: int = 0

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        self.is_work_segment = self.type == SegmentType.WORK
        self.is_break_segment = self.type == SegmentType.BREAK
        self.duration_minutes = int(self.duration_hours * 60)


class WorklogSegmentFilter(BaseModel):
    """Filter for worklog segments."""

    worklog_id: Optional[int] = None
    type: Optional[SegmentType] = None
    is_standard: Optional[bool] = None
    segment_order: Optional[int] = None
