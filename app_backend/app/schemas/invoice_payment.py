"""
InvoicePayment schemas
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class PaymentMethod(str, Enum):
    """Payment method enum"""
    CASH = "CASH"
    CHECK = "CHECK"
    BANK_TRANSFER = "BANK_TRANSFER"
    CREDIT_CARD = "CREDIT_CARD"
    OTHER = "OTHER"


class InvoicePaymentBase(BaseModel):
    """Base payment"""
    payment_date: date = Field(..., description="תאריך תשלום")
    amount: Decimal = Field(..., gt=0, description="סכום")
    payment_method: str = Field(..., max_length=50)


class InvoicePaymentCreate(InvoicePaymentBase):
    """Create payment"""
    invoice_id: int = Field(..., description="חשבונית")
    reference_number: Optional[str] = Field(None, max_length=100)
    transaction_id: Optional[str] = Field(None, max_length=100)
    bank_name: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class InvoicePaymentUpdate(BaseModel):
    """Update payment"""
    payment_date: Optional[date] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    transaction_id: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    notes: Optional[str] = None
    version: Optional[int] = None


class InvoicePaymentResponse(InvoicePaymentBase):
    """Payment response"""
    id: int
    invoice_id: int
    processed_by: Optional[int] = None
    reference_number: Optional[str] = None
    transaction_id: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    deleted_at: Optional[datetime] = None
    version: int
    
    model_config = ConfigDict(from_attributes=True)


class InvoicePaymentBrief(BaseModel):
    """Brief payment"""
    id: int
    invoice_id: int
    payment_date: date
    amount: Decimal
    payment_method: str
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class InvoicePaymentList(BaseModel):
    """List response"""
    items: List[InvoicePaymentResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class InvoicePaymentSearch(BaseModel):
    """Search filters"""
    invoice_id: Optional[int] = Field(None, description="סינון לפי חשבונית")
    payment_method: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    is_active: Optional[bool] = None
    include_deleted: bool = Field(False)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("payment_date")
    sort_desc: bool = Field(True)
