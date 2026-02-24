# app/schemas/activity_log.py
"""Activity log schemas - Complete alignment with model."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ActivityType(str, Enum):
    """Activity type enum - matches model."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    TWO_FA_ENABLED = "2fa_enabled"
    TWO_FA_DISABLED = "2fa_disabled"

    # CRUD Operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

    # Business Actions
    APPROVE = "approve"
    REJECT = "reject"
    SUBMIT = "submit"
    CANCEL = "cancel"
    ASSIGN = "assign"
    UNASSIGN = "unassign"

    # Data Operations
    EXPORT = "export"
    IMPORT = "import"
    DOWNLOAD = "download"
    UPLOAD = "upload"

    # System
    API_CALL = "api_call"
    ERROR = "error"
    WARNING = "warning"


class ActivityLogBase(BaseModel):
    """Base activity log schema."""
    user_id: Optional[int] = Field(None, description="User who performed the activity")
    # Changed to str for flexibility
    activity_type: str = Field(..., description="Type of activity")
    action: str = Field(..., max_length=200, description="Action performed")
    description: Optional[str] = Field(None, description="Detailed description")

    # Entity reference
    entity_type: Optional[str] = Field(None, max_length=50)
    entity_id: Optional[int] = None
    entity_name: Optional[str] = Field(None, max_length=200)

    # Category for role-based filtering
    category: Optional[str] = Field(
        "system", 
        max_length=50,
        description="Activity category: operational, financial, management, system"
    )

    # Request context
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)
    endpoint: Optional[str] = Field(None, max_length=200)
    method: Optional[str] = Field(None, max_length=10)
    status_code: Optional[int] = Field(None, ge=100, le=599)


class ActivityLogCreate(ActivityLogBase):
    """Create activity log entry."""
    metadata: Optional[Dict[str, Any]] = None
    changes: Optional[Dict[str, Any]] = None


class ActivityLogUpdate(BaseModel):
    """Update activity log - rarely used."""
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = Field(None, ge=100, le=599)


class ActivityLogResponse(ActivityLogBase):
    """Activity log response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # From relationships
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    # JSON fields - stored as string in DB, parsed here
    custom_metadata: Optional[Any] = None  # Can be str or dict
    changes: Optional[Any] = None  # Can be str or dict

    model_config = ConfigDict(
        from_attributes=True,
        # Ignore SQLAlchemy internal attributes
        extra='ignore'
    )


class ActivityLogFilter(BaseModel):
    """Filter activity logs."""
    user_id: Optional[int] = None
    user_ids: Optional[List[int]] = None
    activity_type: Optional[ActivityType] = None
    activity_types: Optional[List[ActivityType]] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    ip_address: Optional[str] = None
    search: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    has_errors: Optional[bool] = None


class ActivityStatistics(BaseModel):
    """Activity statistics."""
    total_activities: int = 0
    unique_users: int = 0

    # Breakdowns
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_action: Dict[str, int] = Field(default_factory=dict)
    by_entity_type: Dict[str, int] = Field(default_factory=dict)
    by_hour: Dict[int, int] = Field(default_factory=dict)
    by_day: Dict[str, int] = Field(default_factory=dict)

    # Top lists
    most_active_users: List[Dict[str, Any]] = Field(default_factory=list)
    most_common_actions: List[Dict[str, Any]] = Field(default_factory=list)
    recent_errors: List[Dict[str, Any]] = Field(default_factory=list)

    # Time range
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class UserActivitySummary(BaseModel):
    """User activity summary."""
    user_id: int
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    total_activities: int = 0
    first_activity: Optional[datetime] = None
    last_activity: Optional[datetime] = None

    # Activity breakdown
    activities_by_type: Dict[str, int] = Field(default_factory=dict)
    activities_by_day: Dict[str, int] = Field(default_factory=dict)

    # Recent activity
    recent_activities: List[Dict[str, Any]] = Field(default_factory=list)

    # Login info
    total_logins: int = 0
    failed_logins: int = 0
    last_login: Optional[datetime] = None
    last_login_ip: Optional[str] = None


class SuspiciousActivity(BaseModel):
    """Suspicious activity alert."""
    type: str  # multiple_failed_logins, unusual_hours, mass_export, etc.
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    count: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class ActivityExport(BaseModel):
    """Export configuration."""
    format: str = Field("csv", pattern="^(csv|excel|json)$")
    filters: Optional[ActivityLogFilter] = None
    include_user_details: bool = True
    include_metadata: bool = False
