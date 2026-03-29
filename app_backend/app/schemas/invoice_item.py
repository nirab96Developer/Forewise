"""
InvoiceItem schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class InvoiceItemBase(BaseModel):
    """Base invoice item"""
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)


class InvoiceItemCreate(InvoiceItemBase):
    """Create invoice item"""
    invoice_id: int = Field(..., description="חשבונית (חובה)")
    worklog_id: Optional[int] = None
    line_number: int = Field(..., ge=1)
    item_code: Optional[str] = Field(None, max_length=50)
    discount_percent: Decimal = Field(Decimal('0'), ge=0, le=100)
    discount_amount: Decimal = Field(Decimal('0'), ge=0)
    subtotal: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(Decimal('0.18'), ge=0, le=1)
    tax_amount: Decimal = Field(..., ge=0)
    total: Decimal = Field(..., ge=0)
    notes: Optional[str] = None


class InvoiceItemUpdate(BaseModel):
    """Update invoice item"""
    description: Optional[str] = Field(None, max_length=500)
    item_code: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    subtotal: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    total: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    version: Optional[int] = None


class InvoiceItemResponse(InvoiceItemBase):
    """Invoice item response"""
    id: int
    invoice_id: int
    worklog_id: Optional[int] = None
    line_number: int
    item_code: Optional[str] = None
    discount_percent: Decimal
    discount_amount: Decimal
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_active: bool
    version: int
    
    model_config = ConfigDict(from_attributes=True)


class InvoiceItemBrief(BaseModel):
    """Brief item"""
    id: int
    invoice_id: int
    line_number: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    total: Decimal
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class InvoiceItemList(BaseModel):
    """List response"""
    items: List[InvoiceItemResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class InvoiceItemSearch(BaseModel):
    """Search filters"""
    q: Optional[str] = None
    invoice_id: Optional[int] = Field(None, description="סינון לפי חשבונית")
    worklog_id: Optional[int] = None
    is_active: Optional[bool] = None
    include_deleted: bool = Field(False)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("line_number")
    sort_desc: bool = Field(False)
