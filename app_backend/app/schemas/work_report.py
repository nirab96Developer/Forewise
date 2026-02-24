# /root/app_backend/app/schemas/work_report.py - חדש
"""Work report schemas - Aligned with database model."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkReportType(str, Enum):
    """Work report type - matches model."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    PROJECT = "project"
    EQUIPMENT = "equipment"
    SUPPLIER = "supplier"
    STANDARD = "standard"
    NON_STANDARD = "non_standard"
    OVERTIME = "overtime"
    HOLIDAY = "holiday"


class WorkReportStatus(str, Enum):
    """Work report status - matches model."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class WorkReportBase(BaseModel):
    """Base work report schema."""

    type: WorkReportType = Field(..., description="Report type")
    title: str = Field(..., min_length=1, max_length=200, description="Report title")
    description: Optional[str] = Field(None, description="Report description")

    # Date range
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")

    # User
    user_id: int = Field(..., gt=0, description="Worker ID")

    # Foreign keys
    project_id: Optional[int] = Field(None, gt=0)
    supplier_id: Optional[int] = Field(None, gt=0)
    equipment_id: Optional[int] = Field(None, gt=0)
    work_order_id: Optional[int] = Field(None, gt=0)
    location_id: Optional[int] = Field(None, gt=0)

    # Location
    specific_location: Optional[str] = None
    gps_coordinates: Optional[Dict[str, float]] = None

    # Activity
    activity_type: Optional[str] = Field(None, max_length=100)
    activity_description: Optional[str] = None

    # Hours
    work_hours: Decimal = Field(Decimal("0"), ge=0)
    break_hours: Decimal = Field(Decimal("0"), ge=0)
    overtime_hours: Decimal = Field(Decimal("0"), ge=0)

    # Time
    start_time: Optional[str] = Field(None, pattern="^[0-2][0-9]:[0-5][0-9]$")
    end_time: Optional[str] = Field(None, pattern="^[0-2][0-9]:[0-5][0-9]$")

    # Team
    team_size: int = Field(1, ge=1)

    # Non-standard
    non_standard_reason: Optional[str] = None


class WorkReportCreate(WorkReportBase):
    """Create work report schema."""

    created_by_id: int = Field(..., gt=0)
    status: WorkReportStatus = WorkReportStatus.DRAFT
    custom_metadata_json: Optional[Dict[str, Any]] = None


class WorkReportUpdate(BaseModel):
    """Update work report schema."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[WorkReportStatus] = None
    work_hours: Optional[Decimal] = Field(None, ge=0)
    break_hours: Optional[Decimal] = Field(None, ge=0)
    overtime_hours: Optional[Decimal] = Field(None, ge=0)
    non_standard_reason: Optional[str] = None
    rejection_reason: Optional[str] = None
    is_active: Optional[bool] = None


class WorkReportResponse(WorkReportBase):
    """Work report response schema."""

    id: int
    status: WorkReportStatus
    created_by_id: int

    # Totals
    total_hours: int = 0
    total_workers: int = 0
    total_equipment: int = 0

    # Equipment
    equipment_scanned: bool = False
    scan_time: Optional[datetime] = None
    equipment_hours: Optional[Decimal] = None

    # Workflow
    approved_by_id: Optional[int] = None
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Additional
    hours_breakdown: Optional[dict] = None
    custom_metadata_json: Optional[Dict[str, Any]] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed
    duration_days: int = 0
    is_overdue: bool = False
    can_approve: bool = False

    # From relationships
    created_by_name: Optional[str] = None
    approved_by_name: Optional[str] = None
    user_name: Optional[str] = None
    project_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        self.duration_days = (self.end_date - self.start_date).days + 1
        self.is_overdue = (
            date.today() > self.end_date and self.status == WorkReportStatus.DRAFT
        )
        self.can_approve = self.status == WorkReportStatus.SUBMITTED
