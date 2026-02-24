# /root/app_backend/app/schemas/audit_log.py - מתוקן
"""Audit log schemas - Aligned with database model."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuditAction(str, Enum):
    """Audit action enum - matches model."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    APPROVE = "approve"
    REJECT = "reject"
    EXPORT = "export"
    IMPORT = "import"


class AuditSeverity(str, Enum):
    """Audit severity enum - matches model."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLogBase(BaseModel):
    """Base audit log schema."""

    user_id: Optional[int] = Field(
        None, gt=0, description="User who performed the action"
    )
    action: AuditAction = Field(..., description="Action performed")
    resource: str = Field(..., max_length=100, description="Resource type")
    resource_id: Optional[int] = Field(None, description="Resource ID")
    severity: AuditSeverity = Field(AuditSeverity.LOW, description="Action severity")

    # Request info
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, description="User agent string")

    # Details
    description: Optional[str] = Field(None, description="Action description")

    @field_validator("resource")
    @classmethod
    def validate_resource(cls, v):
        """Validate and normalize resource name."""
        if v:
            return v.lower().replace(" ", "_")
        return v


class AuditLogCreate(AuditLogBase):
    """Schema for creating audit log."""

    old_values: Optional[Dict[str, Any]] = Field(None, description="Previous values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    custom_metadata_json: Optional[Dict[str, Any]] = Field(
        None, description="Custom metadata"
    )


class AuditLogUpdate(BaseModel):
    """Schema for updating audit log - rarely used."""

    description: Optional[str] = None
    custom_metadata_json: Optional[Dict[str, Any]] = None


class AuditLogResponse(AuditLogBase):
    """Audit log response schema."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Change tracking
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    custom_metadata_json: Optional[Dict[str, Any]] = None

    # From relationships
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    # Computed properties
    is_critical: bool = False
    is_high_severity: bool = False
    has_changes: bool = False

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields after initialization."""
        self.is_critical = self.severity == AuditSeverity.CRITICAL
        self.is_high_severity = self.severity in [
            AuditSeverity.HIGH,
            AuditSeverity.CRITICAL,
        ]
        self.has_changes = bool(self.old_values or self.new_values)


class AuditLogFilter(BaseModel):
    """Filter for audit logs."""

    user_id: Optional[int] = None
    user_ids: Optional[List[int]] = None
    action: Optional[AuditAction] = None
    actions: Optional[List[AuditAction]] = None
    resource: Optional[str] = None
    resources: Optional[List[str]] = None
    resource_id: Optional[int] = None
    severity: Optional[AuditSeverity] = None
    severities: Optional[List[AuditSeverity]] = None
    ip_address: Optional[str] = None
    search: Optional[str] = Field(None, description="Search in description")
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


class AuditLogSummary(BaseModel):
    """Audit log summary statistics."""

    total_logs: int = 0
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    # Breakdowns
    by_action: Dict[str, int] = Field(default_factory=dict)
    by_severity: Dict[str, int] = Field(default_factory=dict)
    by_resource: Dict[str, int] = Field(default_factory=dict)
    by_user: Dict[str, int] = Field(default_factory=dict)

    # Security metrics
    critical_actions: int = 0
    high_severity_actions: int = 0
    failed_logins: int = 0
    data_modifications: int = 0
