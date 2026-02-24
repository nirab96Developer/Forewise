# /root/app_backend/app/schemas/daily_work_report.py - חדש
"""Daily work report schemas - Aligned with database model."""
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReportStatus(str, Enum):
    """Report status enum - matches model."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSED = "processed"


class DailyWorkReportBase(BaseModel):
    """Base daily work report schema."""

    worker_id: int = Field(..., gt=0, description="Worker user ID")
    project_id: int = Field(..., gt=0, description="Project ID")
    supplier_id: Optional[int] = Field(None, gt=0, description="Supplier ID")

    work_date: date = Field(..., description="Date of work")

    # Hours tracking
    total_hours: int = Field(0, ge=0, le=24)
    standard_hours: int = Field(0, ge=0, le=24)
    non_standard_hours: int = Field(0, ge=0, le=24)
    break_hours: int = Field(0, ge=0, le=24)
    net_work_hours: int = Field(0, ge=0, le=24)

    # Work details
    activity_summary: Optional[Dict[str, Any]] = Field(
        None, description="Summary of activities"
    )
    equipment_used: Optional[List[str]] = Field(None, description="Equipment used")
    location: Optional[str] = Field(None, description="Work location")
    weather_conditions: Optional[str] = Field(None, max_length=100)

    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator("total_hours")
    @classmethod
    def validate_total_hours(cls, v, info):
        """Validate total hours equals components."""
        data = info.data
        if "standard_hours" in data and "non_standard_hours" in data:
            expected = data["standard_hours"] + data["non_standard_hours"]
            if v != expected:
                raise ValueError(
                    f"Total hours ({v}) must equal standard + non-standard ({expected})"
                )
        return v


class DailyWorkReportCreate(DailyWorkReportBase):
    """Create daily work report schema."""

    status: ReportStatus = ReportStatus.DRAFT


class DailyWorkReportUpdate(BaseModel):
    """Update daily work report schema."""

    total_hours: Optional[int] = Field(None, ge=0, le=24)
    standard_hours: Optional[int] = Field(None, ge=0, le=24)
    non_standard_hours: Optional[int] = Field(None, ge=0, le=24)
    break_hours: Optional[int] = Field(None, ge=0, le=24)
    net_work_hours: Optional[int] = Field(None, ge=0, le=24)
    activity_summary: Optional[Dict[str, Any]] = None
    equipment_used: Optional[List[str]] = None
    location: Optional[str] = None
    weather_conditions: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class DailyWorkReportSubmit(BaseModel):
    """Submit report for approval."""

    notes: Optional[str] = None


class DailyWorkReportApproval(BaseModel):
    """Approve/reject report."""

    action: str = Field(..., pattern="^(approve|reject)$")
    rejection_reason: Optional[str] = Field(None, min_length=1)


class DailyWorkReportResponse(DailyWorkReportBase):
    """Daily work report response schema."""

    id: int
    status: ReportStatus

    # Approval workflow
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by_id: Optional[int] = None
    rejection_reason: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed properties
    is_standard_report: bool = False
    is_approved: bool = False
    is_submitted: bool = False
    can_edit: bool = True

    # From relationships
    worker_name: Optional[str] = None
    project_name: Optional[str] = None
    supplier_name: Optional[str] = None
    approved_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        self.is_standard_report = (
            self.standard_hours > 0 and self.non_standard_hours == 0
        )
        self.is_approved = self.status == ReportStatus.APPROVED
        self.is_submitted = self.status == ReportStatus.SUBMITTED
        self.can_edit = self.status in [ReportStatus.DRAFT, ReportStatus.REJECTED]


class DailyWorkReportFilter(BaseModel):
    """Filter for daily work reports."""

    worker_id: Optional[int] = None
    worker_ids: Optional[List[int]] = None
    project_id: Optional[int] = None
    project_ids: Optional[List[int]] = None
    supplier_id: Optional[int] = None
    status: Optional[ReportStatus] = None
    statuses: Optional[List[ReportStatus]] = None
    work_date: Optional[date] = None
    work_date_from: Optional[date] = None
    work_date_to: Optional[date] = None
    is_standard_report: Optional[bool] = None
    approved_by_id: Optional[int] = None
    min_hours: Optional[int] = None
    max_hours: Optional[int] = None


class DailyWorkReportSummary(BaseModel):
    """Daily work report summary statistics."""

    total_reports: int = 0
    total_hours: int = 0
    standard_hours: int = 0
    non_standard_hours: int = 0

    # By status
    draft_count: int = 0
    submitted_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0

    # By worker
    by_worker: Dict[str, int] = Field(default_factory=dict)

    # By project
    by_project: Dict[str, int] = Field(default_factory=dict)

    # Date range
    from_date: Optional[date] = None
    to_date: Optional[date] = None

    # Averages
    average_hours_per_day: float = 0.0
    average_hours_per_worker: float = 0.0


# Alias for compatibility
DailyReportCreate = DailyWorkReportCreate
DailyReportUpdate = DailyWorkReportUpdate