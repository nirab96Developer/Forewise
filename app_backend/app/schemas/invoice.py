"""
Invoice schemas
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict


class InvoiceStatus(str, Enum):
    """Invoice status enum"""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    SENT = "SENT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class InvoiceBase(BaseModel):
    """Base invoice schema"""
    supplier_id: Optional[int] = Field(None, description="ספק")
    project_id: Optional[int] = Field(None, description="פרויקט")
    issue_date: Optional[date] = Field(None, description="תאריך הנפקה")
    due_date: Optional[date] = Field(None, description="תאריך פירעון")
    subtotal: Optional[Decimal] = Field(None, ge=0, description="סכום לפני מע\"מ")
    tax_amount: Optional[Decimal] = Field(None, ge=0, description="מע\"מ")
    total_amount: Optional[Decimal] = Field(None, ge=0, description="סכום כולל")
    status: Optional[InvoiceStatus] = Field(InvoiceStatus.DRAFT, description="סטטוס")
    notes: Optional[str] = Field(None, description="הערות")


class InvoiceCreate(InvoiceBase):
    """Create invoice"""
    invoice_number: Optional[str] = Field(None, max_length=50, description="מספר חשבונית")
    invoice_date: Optional[date] = Field(None, description="תאריך (alias for issue_date)")
    payment_method: Optional[str] = Field(None, max_length=50)
    paid_amount: Decimal = Field(Decimal('0'), ge=0, description="סכום ששולם")
    work_order_id: Optional[int] = Field(None, description="הזמנת עבודה")
    items: Optional[list] = Field(None, description="שורות חשבונית")

    model_config = ConfigDict(extra='allow')

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: date, info) -> date:
        """Validate due_date >= issue_date"""
        if 'issue_date' in info.data and v < info.data['issue_date']:
            raise ValueError("due_date must be >= issue_date")
        return v

    @field_validator('total_amount')
    @classmethod
    def validate_total_amount(cls, v: Decimal, info) -> Decimal:
        """Validate total_amount = subtotal + tax_amount (if both present)"""
        subtotal = info.data.get('subtotal')
        tax_amount = info.data.get('tax_amount')
        if subtotal is not None and tax_amount is not None:
            expected = subtotal + tax_amount
            if abs(v - expected) > Decimal('0.01'):
                raise ValueError(f"total_amount should equal subtotal + tax_amount (expected {expected}, got {v})")
        return v


class InvoiceUpdate(BaseModel):
    """Update invoice"""
    invoice_number: Optional[str] = Field(None, max_length=50)
    supplier_id: Optional[int] = None
    project_id: Optional[int] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    subtotal: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    paid_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[InvoiceStatus] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    pdf_path: Optional[str] = None
    version: Optional[int] = Field(None, description="גרסה (optimistic locking)")


class InvoiceResponse(InvoiceBase):
    """Invoice response"""
    id: int
    invoice_number: str
    paid_amount: Decimal
    payment_method: Optional[str] = None
    pdf_path: Optional[str] = None
    created_by: Optional[int] = None
    
    # Audit
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_active: bool
    version: int
    
    # Computed
    balance_due: Optional[Decimal] = None
    
    model_config = ConfigDict(from_attributes=True)


class InvoiceBrief(BaseModel):
    """Brief invoice for lists"""
    id: int
    invoice_number: Optional[str] = None
    supplier_id: Optional[int] = None
    project_id: Optional[int] = None
    status: Optional[str] = None
    total_amount: Optional[Decimal] = Decimal("0")
    paid_amount: Optional[Decimal] = Decimal("0")
    due_date: Optional[date] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class InvoiceList(BaseModel):
    """Paginated list"""
    items: List[InvoiceBrief]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class InvoiceSearch(BaseModel):
    """Search filters"""
    q: Optional[str] = Field(None, description="חיפוש (invoice_number, notes)")
    supplier_id: Optional[int] = None
    project_id: Optional[int] = None
    area_id: Optional[int] = None
    status: Optional[InvoiceStatus] = None
    issue_date_from: Optional[date] = None
    issue_date_to: Optional[date] = None
    due_date_from: Optional[date] = None
    due_date_to: Optional[date] = None
    min_total: Optional[Decimal] = Field(None, ge=0)
    max_total: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None
    include_deleted: bool = Field(False)
    
    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("issue_date", description="invoice_number, issue_date, due_date, total_amount")
    sort_desc: bool = Field(True)


class InvoiceStatistics(BaseModel):
    """Statistics"""
    total: int = 0
    total_amount: Decimal = Decimal(0)
    paid_amount: Decimal = Decimal(0)
    balance_due: Decimal = Decimal(0)
    by_status: dict[str, int] = {}
    overdue_count: int = 0
