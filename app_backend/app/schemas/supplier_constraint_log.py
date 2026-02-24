# /root/app_backend/app/schemas/supplier_constraint_log.py - חדש
"""Supplier constraint log schemas - Aligned with database model."""
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConstraintReason(str, Enum):
    """Constraint reason enum - matches model."""

    SUPPLIER_ALREADY_WORKING = "supplier_already_working"
    SPECIFIC_EXPERIENCE = "specific_experience"
    NEARBY_LOCATION = "nearby_location"
    UNIQUE_PROJECT_REQUIREMENT = "unique_project_requirement"
    PRIOR_KNOWLEDGE_OF_AREA = "prior_knowledge_of_area"
    OTHER = "other"


class ConstraintStatus(str, Enum):
    """Constraint status enum - matches model."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class SupplierConstraintLogBase(BaseModel):
    """Base supplier constraint log schema."""

    supplier_id: int = Field(..., gt=0, description="Supplier ID")
    project_id: int = Field(..., gt=0, description="Project ID")

    # Constraint details
    reason: ConstraintReason = Field(..., description="Constraint reason")
    explanation: str = Field(..., min_length=1, description="Detailed explanation")

    # Period
    start_date: date = Field(..., description="Constraint start date")
    duration_days: int = Field(..., gt=0, le=365, description="Duration in days")
    total_hours: int = Field(..., gt=0, description="Total hours")

    # Additional
    notes: Optional[str] = Field(None, description="Additional notes")


class SupplierConstraintLogCreate(SupplierConstraintLogBase):
    """Create supplier constraint log schema."""

    requested_by_id: int = Field(..., gt=0, description="User requesting constraint")
    status: ConstraintStatus = ConstraintStatus.PENDING


class SupplierConstraintLogUpdate(BaseModel):
    """Update supplier constraint log schema."""

    status: Optional[ConstraintStatus] = None
    approved_by_id: Optional[int] = Field(None, gt=0)
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierConstraintLogApproval(BaseModel):
    """Approve/reject constraint."""

    action: str = Field(..., pattern="^(approve|reject)$")
    reason: Optional[str] = Field(None, min_length=1)


class SupplierConstraintLogResponse(SupplierConstraintLogBase):
    """Supplier constraint log response schema."""

    id: int
    requested_by_id: int
    status: ConstraintStatus

    # Approval
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed
    end_date: date = Field(...)
    is_constraint_active: bool = False
    is_approved: bool = False

    # From relationships
    supplier_name: Optional[str] = None
    project_name: Optional[str] = None
    requested_by_name: Optional[str] = None
    approved_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        self.end_date = self.start_date + timedelta(days=self.duration_days)
        today = date.today()
        self.is_constraint_active = (
            self.start_date <= today <= self.end_date
            and self.status == ConstraintStatus.APPROVED
        )
        self.is_approved = self.status == ConstraintStatus.APPROVED
