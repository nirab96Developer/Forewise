# app/schemas/milestone.py
"""Milestone schemas."""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MilestoneStatus(str, Enum):
    """Milestone status."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class MilestonePriority(str, Enum):
    """Milestone priority."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MilestoneType(str, Enum):
    """Milestone type."""
    DELIVERABLE = "deliverable"
    MILESTONE = "milestone"
    PHASE = "phase"
    REVIEW = "review"
    APPROVAL = "approval"


class MilestoneBase(BaseModel):
    """Base milestone schema."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    project_id: int = Field(..., gt=0)
    planned_date: date
    priority: MilestonePriority = MilestonePriority.MEDIUM
    depends_on_milestone_id: Optional[int] = Field(None, gt=0)
    assigned_to: Optional[int] = Field(None, gt=0)
    requires_verification: bool = False


class MilestoneCreate(MilestoneBase):
    """Create milestone schema."""
    pass


class MilestoneUpdate(BaseModel):
    """Update milestone schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    status: Optional[MilestoneStatus] = None
    priority: Optional[MilestonePriority] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    assigned_to: Optional[int] = Field(None, gt=0)
    completion_notes: Optional[str] = None


class MilestoneResponse(MilestoneBase):
    """Milestone response schema."""
    id: int
    actual_date: Optional[date] = None
    status: MilestoneStatus
    progress_percentage: float
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    completion_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # From relationships
    project_name: Optional[str] = None
    assigned_user_name: Optional[str] = None
    verified_user_name: Optional[str] = None
    
    # Computed
    is_overdue: bool = False
    days_until_due: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class MilestoneVerify(BaseModel):
    """Verify milestone completion."""
    notes: Optional[str] = None
