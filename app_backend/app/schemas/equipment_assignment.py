# /root/app_backend/app/schemas/equipment_assignment.py - חדש
"""Equipment assignment schemas - Aligned with database model."""
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssignmentStatus(str, Enum):
    """Assignment status enum - matches model."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class EquipmentAssignmentBase(BaseModel):
    """Base equipment assignment schema."""

    equipment_id: int = Field(..., gt=0, description="Equipment ID")
    project_id: int = Field(..., gt=0, description="Project ID")

    # Assignment period
    start_date: date = Field(..., description="Assignment start date")
    end_date: Optional[date] = Field(None, description="Assignment end date")
    expected_hours: Optional[int] = Field(
        None, ge=0, description="Expected hours of use"
    )

    # Details
    location: Optional[str] = Field(None, description="Assignment location")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v, info):
        """Ensure end_date is after start_date."""
        if v and "start_date" in info.data:
            if v < info.data["start_date"]:
                raise ValueError("End date must be after start date")
        return v


class EquipmentAssignmentCreate(EquipmentAssignmentBase):
    """Create equipment assignment schema."""

    assigned_by_id: int = Field(
        ..., gt=0, description="User who assigned the equipment"
    )
    status: AssignmentStatus = AssignmentStatus.PENDING


class EquipmentAssignmentUpdate(BaseModel):
    """Update equipment assignment schema."""

    start_date: Optional[date] = None
    end_date: Optional[date] = None
    expected_hours: Optional[int] = Field(None, ge=0)
    location: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[AssignmentStatus] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    actual_hours: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class EquipmentAssignmentResponse(EquipmentAssignmentBase):
    """Equipment assignment response schema."""

    id: int
    assigned_by_id: int
    status: AssignmentStatus

    # Actual tracking
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    actual_hours: int = 0

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed properties
    is_assignment_active: bool = False
    is_overdue: bool = False
    duration_days: Optional[int] = None

    # From relationships
    equipment_name: Optional[str] = None
    equipment_code: Optional[str] = None
    project_name: Optional[str] = None
    project_code: Optional[str] = None
    assigned_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        today = date.today()
        self.is_assignment_active = self.start_date <= today and (
            not self.end_date or today <= self.end_date
        )
        self.is_overdue = (
            self.end_date
            and today > self.end_date
            and self.status == AssignmentStatus.ACTIVE
        )
        if self.end_date:
            self.duration_days = (self.end_date - self.start_date).days


class EquipmentAssignmentFilter(BaseModel):
    """Filter for equipment assignments."""

    equipment_id: Optional[int] = None
    equipment_ids: Optional[list[int]] = None
    project_id: Optional[int] = None
    project_ids: Optional[list[int]] = None
    assigned_by_id: Optional[int] = None
    status: Optional[AssignmentStatus] = None
    statuses: Optional[list[AssignmentStatus]] = None
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    end_date_from: Optional[date] = None
    end_date_to: Optional[date] = None
    is_assignment_active: Optional[bool] = None
    is_overdue: Optional[bool] = None


class EquipmentAssignmentSummary(BaseModel):
    """Equipment assignment summary statistics."""

    total_assignments: int = 0

    # By status
    pending_count: int = 0
    active_count: int = 0
    completed_count: int = 0
    cancelled_count: int = 0
    overdue_count: int = 0

    # Hours
    total_expected_hours: int = 0
    total_actual_hours: int = 0

    # Utilization
    average_duration_days: float = 0.0
    utilization_rate: float = 0.0


# Alias for compatibility
AssignmentCreate = EquipmentAssignmentCreate
AssignmentUpdate = EquipmentAssignmentUpdate
AssignmentResponse = EquipmentAssignmentResponse