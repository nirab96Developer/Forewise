# /root/app_backend/app/schemas/balance_release.py - מתוקן
"""Balance release schemas - Aligned with database model."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReleaseType(str, Enum):
    """Release type enum - matches model."""

    SCHEDULED = "scheduled"
    ON_DEMAND = "on_demand"
    EMERGENCY = "emergency"
    APPROVAL_BASED = "approval_based"
    AUTOMATIC = "automatic"


class ReleaseStatus(str, Enum):
    """Release status enum - matches model."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSED = "processed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BalanceReleaseBase(BaseModel):
    """Base balance release schema."""

    budget_id: int = Field(..., gt=0, description="Parent budget ID")
    release_type: ReleaseType = Field(..., description="Type of release")
    amount: Decimal = Field(..., gt=0, description="Release amount")
    description: str = Field(..., min_length=1, description="Release description")
    release_date: date = Field(..., description="Scheduled release date")
    expiry_date: Optional[date] = Field(None, description="Expiry date if applicable")
    requires_approval: bool = Field(True, description="Whether approval is required")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount is positive."""
        if v <= 0:
            raise ValueError("Release amount must be positive")
        return v


class BalanceReleaseCreate(BalanceReleaseBase):
    """Create balance release schema."""

    pass


class BalanceReleaseUpdate(BaseModel):
    """Update balance release schema."""

    amount: Optional[Decimal] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=1)
    release_date: Optional[date] = None
    expiry_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class BalanceReleaseApproval(BaseModel):
    """Approve or reject balance release."""

    action: str = Field(..., pattern="^(approve|reject)$")
    rejection_reason: Optional[str] = Field(None, min_length=1)
    notes: Optional[str] = None


class BalanceReleaseResponse(BalanceReleaseBase):
    """Balance release response schema."""

    id: int
    status: ReleaseStatus

    # Processing info
    processed_date: Optional[datetime] = None

    # Approval info
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed properties
    is_approved: bool = False
    is_processed: bool = False
    is_pending: bool = True
    is_overdue: bool = False
    is_expired: bool = False
    days_until_release: int = 0

    # From relationships
    budget_name: Optional[str] = None
    approved_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        self.is_approved = self.status == ReleaseStatus.APPROVED
        self.is_processed = self.status == ReleaseStatus.PROCESSED
        self.is_pending = self.status == ReleaseStatus.PENDING
        self.is_overdue = date.today() > self.release_date and self.is_pending
        self.is_expired = self.status == ReleaseStatus.EXPIRED
        if self.release_date:
            self.days_until_release = max(0, (self.release_date - date.today()).days)


class BalanceReleaseFilter(BaseModel):
    """Filter for balance releases."""

    budget_id: Optional[int] = None
    budget_ids: Optional[List[int]] = None
    release_type: Optional[ReleaseType] = None
    release_types: Optional[List[ReleaseType]] = None
    status: Optional[ReleaseStatus] = None
    statuses: Optional[List[ReleaseStatus]] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    release_date_from: Optional[date] = None
    release_date_to: Optional[date] = None
    requires_approval: Optional[bool] = None
    approved_by_id: Optional[int] = None
    search: Optional[str] = Field(None, description="Search in description and notes")


class BalanceReleaseSummary(BaseModel):
    """Balance release summary statistics."""

    total_releases: int = 0
    total_amount: Decimal = Decimal("0.00")

    # By status
    pending_count: int = 0
    pending_amount: Decimal = Decimal("0.00")
    approved_count: int = 0
    approved_amount: Decimal = Decimal("0.00")
    processed_count: int = 0
    processed_amount: Decimal = Decimal("0.00")

    # By type
    by_type: dict = Field(default_factory=dict)

    # Upcoming
    upcoming_releases: List[dict] = Field(default_factory=list)
    overdue_releases: List[dict] = Field(default_factory=list)


# Alias for compatibility
ReleaseCreate = BalanceReleaseCreate
ReleaseUpdate = BalanceReleaseUpdate
ReleaseResponse = BalanceReleaseResponse