"""Payment schemas - Aligned with database model."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field, field_validator


class PaymentStatus(str, Enum):
    """Payment status enum - matches model."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """Payment method enum - matches model."""

    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    DIGITAL_WALLET = "digital_wallet"


class PaymentBase(PydanticBaseModel):
    """Base payment schema."""
    
    model_config = ConfigDict(from_attributes=True)

    invoice_id: int = Field(..., gt=0, description="Invoice ID")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    payment_date: datetime = Field(..., description="Payment date")
    reference_number: Optional[str] = Field(None, max_length=100, description="Reference number")
    notes: Optional[str] = Field(None, max_length=500, description="Payment notes")
    status: PaymentStatus = Field(PaymentStatus.PENDING, description="Payment status")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """Validate payment amount."""
        if v <= 0:
            raise ValueError("Payment amount must be positive")
        return v


class PaymentCreate(PaymentBase):
    """Create payment schema."""

    processed_by_id: int = Field(..., gt=0, description="User who processed payment")


class PaymentUpdate(PydanticBaseModel):
    """Update payment schema."""
    
    model_config = ConfigDict(from_attributes=True)

    amount: Optional[Decimal] = Field(None, gt=0)
    payment_method: Optional[PaymentMethod] = None
    payment_date: Optional[datetime] = None
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    status: Optional[PaymentStatus] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """Validate payment amount."""
        if v is not None and v <= 0:
            raise ValueError("Payment amount must be positive")
        return v


class PaymentSummaryResponse(PaymentBase):
    """Abbreviated payment response (list views)."""

    id: int
    processed_by_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    invoice_number: Optional[str] = None
    processed_by_name: Optional[str] = None


class PaymentStatistics(PydanticBaseModel):
    """Payment statistics schema."""

    total_payments: int = 0
    total_amount: Decimal = Decimal("0")
    pending_payments: int = 0
    completed_payments: int = 0
    failed_payments: int = 0

    # By method
    by_method: dict = Field(default_factory=dict)

    # By status
    by_status: dict = Field(default_factory=dict)

    # Recent
    today_amount: Decimal = Decimal("0")
    week_amount: Decimal = Decimal("0")
    month_amount: Decimal = Decimal("0")


class PaymentBatchRequest(PydanticBaseModel):
    """Payment batch request schema."""
    
    model_config = ConfigDict(from_attributes=True)

    invoice_ids: List[int] = Field(..., min_items=1, description="List of invoice IDs")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    payment_date: datetime = Field(..., description="Payment date")
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    processed_by_id: int = Field(..., gt=0, description="User processing payments")


class PaymentSummary(PydanticBaseModel):
    """Payment summary schema."""
    
    model_config = ConfigDict(from_attributes=True)

    total_payments: int = 0
    total_amount: Decimal = Decimal("0")
    pending_amount: Decimal = Decimal("0")
    completed_amount: Decimal = Decimal("0")
    failed_amount: Decimal = Decimal("0")
    
    # By method
    by_method: Dict[str, Decimal] = Field(default_factory=dict)
    
    # By status
    by_status: Dict[str, int] = Field(default_factory=dict)
    
    # Recent
    today_count: int = 0
    today_amount: Decimal = Decimal("0")
    week_count: int = 0
    week_amount: Decimal = Decimal("0")


class PaymentResponse(PydanticBaseModel):
    """Payment response schema."""
    
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int
    amount: Decimal
    payment_method: PaymentMethod
    payment_date: datetime
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    status: PaymentStatus
    processed_by_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # From relationships
    invoice_number: Optional[str] = None
    processed_by_name: Optional[str] = None
