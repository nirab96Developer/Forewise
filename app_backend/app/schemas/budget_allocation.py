# /root/app_backend/app/schemas/budget_allocation.py - חדש
"""Budget allocation schemas - Aligned with database model."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AllocationType(str, Enum):
    """Allocation type enum - matches model."""

    PROJECT = "project"
    AREA = "area"
    DEPARTMENT = "department"
    EQUIPMENT = "equipment"
    EMERGENCY = "emergency"


class AllocationStatus(str, Enum):
    """Allocation status enum - matches model."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RELEASED = "released"
    CANCELLED = "cancelled"


class BudgetAllocationBase(BaseModel):
    """Base budget allocation schema."""

    budget_id: int = Field(..., gt=0, description="Source budget ID")
    allocation_type: AllocationType = Field(..., description="Type of allocation")

    # Recipients (at least one required)
    project_id: Optional[int] = Field(None, gt=0, description="Target project")
    area_id: Optional[int] = Field(None, gt=0, description="Target area")
    department_id: Optional[int] = Field(None, gt=0, description="Target department")

    amount: Decimal = Field(..., gt=0, description="Allocation amount")
    description: str = Field(..., min_length=1, max_length=500)
    justification: Optional[str] = Field(
        None, description="Justification for allocation"
    )

    allocation_date: date = Field(..., description="Allocation date")
    release_date: Optional[date] = Field(None, description="Planned release date")
    expiry_date: Optional[date] = Field(None, description="Expiry date")

    is_recurring: bool = Field(False, description="Is this a recurring allocation")
    requires_approval: bool = Field(True, description="Requires approval")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount is positive."""
        if v <= 0:
            raise ValueError("Allocation amount must be positive")
        return v


class BudgetAllocationCreate(BudgetAllocationBase):
    """Create budget allocation schema."""

    requested_by_id: int = Field(..., gt=0, description="Requester ID")


class BudgetAllocationUpdate(BaseModel):
    """Update budget allocation schema."""

    amount: Optional[Decimal] = Field(None, gt=0)
    released_amount: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    justification: Optional[str] = None
    release_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[AllocationStatus] = None
    is_active: Optional[bool] = None


class BudgetAllocationApproval(BaseModel):
    """Approve/reject allocation."""

    action: str = Field(..., pattern="^(approve|reject|cancel)$")
    notes: Optional[str] = None


class BudgetAllocationResponse(BudgetAllocationBase):
    """Budget allocation response schema."""

    id: int
    status: AllocationStatus
    released_amount: Decimal = Field(Decimal("0"), description="Amount released")

    # Approval info
    requested_by_id: int
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed
    remaining_amount: Decimal = Field(Decimal("0"), description="Amount remaining")
    is_fully_released: bool = False

    # From relationships
    budget_name: Optional[str] = None
    project_name: Optional[str] = None
    area_name: Optional[str] = None
    department_name: Optional[str] = None
    requested_by_name: Optional[str] = None
    approved_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        self.remaining_amount = self.amount - self.released_amount
        self.is_fully_released = self.released_amount >= self.amount


class BudgetAllocationFilter(BaseModel):
    """Filter for budget allocations."""

    budget_id: Optional[int] = None
    allocation_type: Optional[AllocationType] = None
    project_id: Optional[int] = None
    area_id: Optional[int] = None
    department_id: Optional[int] = None
    status: Optional[AllocationStatus] = None
    requested_by_id: Optional[int] = None
    approved_by_id: Optional[int] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    is_recurring: Optional[bool] = None
    requires_approval: Optional[bool] = None


class BudgetAllocationSummary(BaseModel):
    """Allocation summary statistics."""

    total_allocations: int = 0
    total_amount: Decimal = Decimal("0")
    released_amount: Decimal = Decimal("0")
    remaining_amount: Decimal = Decimal("0")

    # By status
    pending_count: int = 0
    approved_count: int = 0
    released_count: int = 0

    # By type
    by_type: dict = Field(default_factory=dict)
