# /root/app_backend/app/schemas/work_break.py - חדש
"""Work break schemas - Aligned with database model."""
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BreakType(str, Enum):
    """Break type - matches model."""

    LUNCH = "lunch"
    COFFEE = "coffee"
    REST = "rest"
    MEETING = "meeting"
    OTHER = "other"


class WorkBreakBase(BaseModel):
    """Base work break schema."""

    worklog_id: int = Field(..., gt=0, description="Worklog ID")

    # Break timing
    break_date: date = Field(..., description="Break date")
    start_time: time = Field(..., description="Break start time")
    end_time: time = Field(..., description="Break end time")

    # Break details
    type: BreakType = Field(..., description="Break type")
    duration_hours: Decimal = Field(..., ge=0, le=24, description="Duration in hours")

    # Additional
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=100)
    is_standard: bool = Field(True, description="Is standard break")
    notes: Optional[str] = None


class WorkBreakCreate(WorkBreakBase):
    """Create work break schema."""

    pass


class WorkBreakUpdate(BaseModel):
    """Update work break schema."""

    break_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    type: Optional[BreakType] = None
    duration_hours: Optional[Decimal] = Field(None, ge=0, le=24)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=100)
    is_standard: Optional[bool] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class WorkBreakResponse(WorkBreakBase):
    """Work break response schema."""

    id: int

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed
    duration_minutes: int = 0
    is_standard_break: bool = False

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        self.duration_minutes = int(self.duration_hours * 60)
        self.is_standard_break = self.is_standard and self.duration_hours == Decimal(
            "0.5"
        )


class WorkBreakFilter(BaseModel):
    """Filter for work breaks."""

    worklog_id: Optional[int] = None
    type: Optional[BreakType] = None
    break_date: Optional[date] = None
    is_standard: Optional[bool] = None
