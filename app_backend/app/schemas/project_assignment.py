# /root/app_backend/app/schemas/project_assignment.py - חדש
"""Project assignment schemas - Aligned with database model."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, List

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectRole(str, Enum):
    """Project role enum - matches model."""

    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    WORKER = "worker"
    INSPECTOR = "inspector"
    CONSULTANT = "consultant"
    VIEWER = "viewer"


class AssignmentStatus(str, Enum):
    """Assignment status enum - matches model."""

    ACTIVE = "active"
    PENDING = "pending"
    COMPLETED = "completed"
    SUSPENDED = "suspended"


class ProjectAssignmentBase(BaseModel):
    """Base project assignment schema."""

    project_id: int = Field(..., gt=0, description="Project ID")
    user_id: int = Field(..., gt=0, description="User ID")

    # Role and status
    role: ProjectRole = Field(ProjectRole.WORKER, description="Role in project")

    # Assignment period
    start_date: date = Field(..., description="Assignment start date")
    end_date: Optional[date] = Field(None, description="Assignment end date")

    # Work allocation
    allocation_percentage: int = Field(
        100, ge=0, le=100, description="Allocation percentage"
    )
    estimated_hours: Optional[float] = Field(None, ge=0, description="Estimated hours")

    # Permissions
    can_approve_reports: bool = Field(False, description="Can approve reports")
    can_manage_team: bool = Field(False, description="Can manage team")
    can_edit_budget: bool = Field(False, description="Can edit budget")

    # Assignment details
    responsibilities: Optional[str] = Field(None, description="Responsibilities")
    notes: Optional[str] = Field(None, description="Notes")

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v, info):
        """Ensure end_date is after start_date."""
        if v and "start_date" in info.data:
            if v < info.data["start_date"]:
                raise ValueError("End date must be after start date")
        return v


class ProjectAssignmentCreate(ProjectAssignmentBase):
    """Create project assignment schema."""

    status: AssignmentStatus = AssignmentStatus.PENDING


class ProjectAssignmentUpdate(BaseModel):
    """Update project assignment schema."""

    role: Optional[ProjectRole] = None
    status: Optional[AssignmentStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    allocation_percentage: Optional[int] = Field(None, ge=0, le=100)
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    can_approve_reports: Optional[bool] = None
    can_manage_team: Optional[bool] = None
    can_edit_budget: Optional[bool] = None
    responsibilities: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectAssignmentApproval(BaseModel):
    """Approve/reject assignment."""

    action: str = Field(..., pattern="^(approve|reject|suspend)$")
    notes: Optional[str] = None


class ProjectAssignmentResponse(ProjectAssignmentBase):
    """Project assignment response schema."""

    id: int
    status: AssignmentStatus

    # Work tracking
    actual_hours: Optional[float] = None

    # Approval
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed properties
    is_currently_active: bool = False
    duration_days: Optional[int] = None
    hours_utilization: Optional[float] = None

    # From relationships
    project_name: Optional[str] = None
    project_code: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    approved_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        # Check if currently active
        if self.status == AssignmentStatus.ACTIVE:
            today = date.today()
            self.is_currently_active = self.start_date <= today and (
                not self.end_date or self.end_date >= today
            )
        else:
            self.is_currently_active = False

        # Calculate duration
        if self.end_date:
            self.duration_days = (self.end_date - self.start_date).days + 1

        # Calculate utilization
        if self.estimated_hours and self.estimated_hours > 0 and self.actual_hours:
            self.hours_utilization = (self.actual_hours / self.estimated_hours) * 100


class ProjectAssignmentFilter(BaseModel):
    """Filter for project assignments."""

    project_id: Optional[int] = None
    project_ids: Optional[list[int]] = None
    user_id: Optional[int] = None
    user_ids: Optional[list[int]] = None
    role: Optional[ProjectRole] = None
    roles: Optional[list[ProjectRole]] = None
    status: Optional[AssignmentStatus] = None
    statuses: Optional[list[AssignmentStatus]] = None
    can_approve_reports: Optional[bool] = None
    can_manage_team: Optional[bool] = None
    can_edit_budget: Optional[bool] = None
    is_currently_active: Optional[bool] = None
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    end_date_from: Optional[date] = None
    end_date_to: Optional[date] = None


class ProjectAssignmentSummary(BaseModel):
    """Project assignment summary statistics."""

    total_assignments: int = 0

    # By status
    active_count: int = 0
    pending_count: int = 0
    completed_count: int = 0
    suspended_count: int = 0

    # By role
    by_role: dict = Field(default_factory=dict)

    # Allocation
    total_allocated_hours: float = 0
    total_actual_hours: float = 0
    average_allocation_percentage: float = 0

    # Permissions
    with_approval_rights: int = 0
    with_team_management: int = 0
    with_budget_edit: int = 0


# Alias for compatibility
AssignmentCreate = ProjectAssignmentCreate
AssignmentResponse = ProjectAssignmentResponse
AssignmentUpdate = ProjectAssignmentUpdate


class AssignmentStatistics(BaseModel):
    """Assignment statistics schema."""
    
    total_assignments: int = 0
    active_assignments: int = 0
    completed_assignments: int = 0
    suspended_assignments: int = 0
    
    # By role
    by_role: Dict[str, int] = Field(default_factory=dict)
    
    # By status
    by_status: Dict[str, int] = Field(default_factory=dict)
    
    # Hours
    total_allocated_hours: float = 0
    total_actual_hours: float = 0
    average_allocation_percentage: float = 0
    
    # Permissions
    with_approval_rights: int = 0
    with_team_management: int = 0
    with_budget_edit: int = 0


class ProjectTeamResponse(BaseModel):
    """Project team response schema."""
    
    project_id: int
    project_name: Optional[str] = None
    
    # Team members
    team_members: List[dict] = Field(default_factory=list)
    
    # Statistics
    total_members: int = 0
    active_members: int = 0
    
    # By role
    by_role: Dict[str, int] = Field(default_factory=dict)
    
    # Permissions summary
    with_approval_rights: int = 0
    with_team_management: int = 0
    with_budget_edit: int = 0


class UserProjectsResponse(BaseModel):
    """User projects response schema."""
    
    user_id: int
    user_name: Optional[str] = None
    
    # Projects
    projects: List[dict] = Field(default_factory=list)
    
    # Statistics
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    
    # By role
    by_role: Dict[str, int] = Field(default_factory=dict)
    
    # Hours
    total_allocated_hours: float = 0
    total_actual_hours: float = 0