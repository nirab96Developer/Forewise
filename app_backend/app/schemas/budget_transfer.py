# /root/app_backend/app/schemas/budget_transfer.py - חדש
"""Budget transfer schemas - Aligned with database model."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransferStatus(str, Enum):
    """Transfer status enum - matches model."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TransferType(str, Enum):
    """Transfer type enum - matches model."""

    REGULAR = "regular"
    EMERGENCY = "emergency"
    REALLOCATION = "reallocation"
    RETURN = "return"


class BudgetTransferBase(BaseModel):
    """Base budget transfer schema."""

    # Source
    source_budget_id: int = Field(..., gt=0, description="Source budget ID")
    source_item_id: Optional[int] = Field(
        None, gt=0, description="Source budget item ID"
    )

    # Target
    target_budget_id: int = Field(..., gt=0, description="Target budget ID")
    target_item_id: Optional[int] = Field(
        None, gt=0, description="Target budget item ID"
    )

    # Transfer details
    transfer_type: TransferType = Field(
        TransferType.REGULAR, description="Type of transfer"
    )
    amount: Decimal = Field(..., gt=0, description="Transfer amount")

    # Reason
    reason: str = Field(
        ..., min_length=1, max_length=500, description="Transfer reason"
    )
    justification: Optional[str] = Field(None, description="Detailed justification")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount is positive."""
        if v <= 0:
            raise ValueError("Transfer amount must be positive")
        return v


class BudgetTransferCreate(BudgetTransferBase):
    """Create budget transfer schema."""

    requested_by_id: int = Field(..., gt=0, description="Requester ID")
    requested_at: datetime = Field(default_factory=datetime.utcnow)


class BudgetTransferUpdate(BaseModel):
    """Update budget transfer schema."""

    amount: Optional[Decimal] = Field(None, gt=0)
    reason: Optional[str] = Field(None, min_length=1, max_length=500)
    justification: Optional[str] = None
    status: Optional[TransferStatus] = None
    is_active: Optional[bool] = None


class BudgetTransferApproval(BaseModel):
    """Approve/reject transfer."""

    action: str = Field(..., pattern="^(approve|reject|cancel)$")
    notes: Optional[str] = None


class BudgetTransferResponse(BudgetTransferBase):
    """Budget transfer response schema."""

    id: int
    status: TransferStatus

    # Timestamps
    requested_at: datetime
    executed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Users
    requested_by_id: int
    approved_by_id: Optional[int] = None

    # Status
    is_active: bool = True

    # From relationships
    source_budget_name: Optional[str] = None
    source_item_name: Optional[str] = None
    target_budget_name: Optional[str] = None
    target_item_name: Optional[str] = None
    requested_by_name: Optional[str] = None
    approved_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BudgetTransferFilter(BaseModel):
    """Filter for budget transfers."""

    source_budget_id: Optional[int] = None
    source_item_id: Optional[int] = None
    target_budget_id: Optional[int] = None
    target_item_id: Optional[int] = None
    transfer_type: Optional[TransferType] = None
    status: Optional[TransferStatus] = None
    requested_by_id: Optional[int] = None
    approved_by_id: Optional[int] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    search: Optional[str] = Field(
        None, description="Search in reason and justification"
    )


class BudgetTransferSummary(BaseModel):
    """Budget transfer summary statistics."""

    total_transfers: int = 0
    total_amount: Decimal = Decimal("0")

    # By status
    pending_count: int = 0
    pending_amount: Decimal = Decimal("0")
    approved_count: int = 0
    approved_amount: Decimal = Decimal("0")
    completed_count: int = 0
    completed_amount: Decimal = Decimal("0")

    # By type
    by_type: dict = Field(default_factory=dict)

    # Recent
    recent_transfers: list = Field(default_factory=list)
