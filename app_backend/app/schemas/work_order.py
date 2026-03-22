"""
WorkOrder schemas - SYNCED WITH DB MODEL - 17.11.2025
order_number is Integer, status/priority are String
"""
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict, model_validator


class WorkOrderFilters(BaseModel):
    """Filters for work order queries"""
    status: Optional[str] = None
    priority: Optional[str] = None
    project_id: Optional[int] = None
    supplier_id: Optional[int] = None
    location_id: Optional[int] = None
    equipment_type: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class CalendarEventResponse(BaseModel):
    """Calendar event response for work orders"""
    id: int
    title: str
    start: datetime
    end: Optional[datetime] = None
    color: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class WorkOrderBase(BaseModel):
    """Base work order schema - SYNCED WITH DB"""
    
    # Basic info - order_number is Integer!
    order_number: int = Field(..., description="Order number")
    title: Optional[str] = Field(None, max_length=255, description="Title")
    description: Optional[str] = Field(None, description="Description")
    
    # Foreign keys
    project_id: Optional[int] = Field(None, description="Project ID")
    supplier_id: Optional[int] = Field(None, description="Supplier ID")
    equipment_id: Optional[int] = Field(None, description="Equipment ID")
    location_id: Optional[int] = Field(None, description="Location ID")
    
    # Work details
    equipment_type: Optional[str] = Field(None, max_length=100, description="Equipment type")
    work_start_date: Optional[date] = Field(None, description="Work start date")
    work_end_date: Optional[date] = Field(None, description="Work end date")
    
    # Status and priority - String, not Enum!
    status: Optional[str] = Field("pending", max_length=50, description="Status")
    priority: Optional[str] = Field("medium", max_length=20, description="Priority")
    
    # Portal integration
    portal_token: Optional[str] = Field(None, max_length=255)
    portal_token_expires: Optional[datetime] = None
    portal_expiry: Optional[datetime] = None  # NEW!
    response_received_at: Optional[datetime] = None  # NEW!
    token_expires_at: Optional[datetime] = None  # NEW!
    supplier_response_at: Optional[datetime] = None  # NEW!
    
    # Financial
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    actual_hours: Optional[Decimal] = Field(None, ge=0)
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    
    # Constraints and rejections - NEW!
    constraint_reason_id: Optional[int] = None
    constraint_notes: Optional[str] = None
    rejection_reason_id: Optional[int] = None
    rejection_notes: Optional[str] = None
    is_forced_selection: Optional[bool] = False


class WorkOrderCreate(BaseModel):
    """Create work order schema - order_number is auto-generated."""
    
    # order_number is NOT required on create - it's auto-generated
    title: Optional[str] = Field(None, max_length=255, description="Title")
    description: Optional[str] = Field(None, description="Description")
    
    # Foreign keys
    project_id: Optional[int] = Field(None, description="Project ID")
    supplier_id: Optional[int] = Field(None, description="Supplier ID")
    equipment_id: Optional[int] = Field(None, description="Equipment ID")
    location_id: Optional[int] = Field(None, description="Location ID")
    requested_equipment_model_id: Optional[int] = Field(None, description="Requested equipment model ID")
    
    # Work details
    equipment_type: Optional[str] = Field(None, max_length=100, description="Equipment type")
    work_start_date: Optional[date] = Field(None, description="Work start date")
    work_end_date: Optional[date] = Field(None, description="Work end date")
    
    # Status and priority
    status: Optional[str] = Field("pending", max_length=50, description="Status")
    priority: Optional[str] = Field("medium", max_length=20, description="Priority")
    
    # Financial
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    
    # Constraints
    constraint_reason_id: Optional[int] = None
    constraint_notes: Optional[str] = None
    is_forced_selection: Optional[bool] = False

    # Overnight guard (שמירת לילה)
    requires_guard: Optional[bool] = False
    guard_days: Optional[int] = 0

    # Planning / billing (DB model)
    days: Optional[int] = Field(None, ge=0, description="מספר ימי עבודה")
    has_overnight: Optional[bool] = False
    overnight_nights: Optional[int] = Field(0, ge=0)
    allocation_method: Optional[str] = Field(
        None, max_length=20, description="FAIR_ROTATION | MANUAL"
    )
    total_amount: Optional[Decimal] = Field(None, ge=0)
    frozen_amount: Optional[Decimal] = Field(None, ge=0)


class WorkOrderUpdate(BaseModel):
    """Update work order schema - all fields optional."""
    
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, max_length=20)
    supplier_id: Optional[int] = None
    work_start_date: Optional[date] = None
    work_end_date: Optional[date] = None
    estimated_hours: Optional[Decimal] = None
    actual_hours: Optional[Decimal] = None
    constraint_reason_id: Optional[int] = None
    constraint_notes: Optional[str] = None
    rejection_reason_id: Optional[int] = None
    rejection_notes: Optional[str] = None


class WorkOrderResponse(WorkOrderBase):
    """Work order response schema."""
    
    id: int
    order_number: Optional[int] = None
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    requested_equipment_model_id: Optional[int] = None
    requires_guard: Optional[bool] = False
    guard_days: Optional[int] = 0
    portal_token: Optional[str] = None
    
    # From relationships
    project_name: Optional[str] = None
    supplier_name: Optional[str] = None
    equipment_name: Optional[str] = None
    location_name: Optional[str] = None
    area_name: Optional[str] = None
    region_name: Optional[str] = None

    # Planning / billing
    days: Optional[int] = None
    has_overnight: Optional[bool] = False
    overnight_nights: Optional[int] = 0
    allocation_method: Optional[str] = None
    frozen_amount: Optional[Decimal] = None
    remaining_frozen: Optional[Decimal] = None
    charged_amount: Optional[Decimal] = None

    # Computed hours tracking (enriched by endpoint)
    used_hours: Optional[float] = None
    remaining_hours: Optional[float] = None
    days_total: Optional[float] = None
    days_used: Optional[float] = None
    days_remaining: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)



class WorkOrderFilter(BaseModel):
    """Filter for work orders - types are String!"""
    
    search: Optional[str] = Field(None, description="Search")
    status: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, max_length=20)
    project_id: Optional[int] = None
    supplier_id: Optional[int] = None
    equipment_id: Optional[int] = None
    location_id: Optional[int] = None


class WorkOrderBrief(BaseModel):
    """Minimal work order summary for lists and references."""
    id: int
    order_number: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    project_id: Optional[int] = None
    supplier_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class WorkOrderList(BaseModel):
    """Paginated work order list response."""
    items: List[WorkOrderResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 50
    total_pages: int = 0
    model_config = ConfigDict(from_attributes=True)


class WorkOrderSearch(BaseModel):
    search: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    project_id: Optional[int] = None
    supplier_id: Optional[int] = None
    area_id: Optional[int] = None
    page: int = 1
    page_size: int = 50
    per_page: Optional[int] = None  # alias for page_size (frontend compatibility)


class WorkOrderStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class WorkOrderApproveRequest(BaseModel):
    notes: Optional[str] = None


class WorkOrderRejectRequest(BaseModel):
    reason: str
    notes: Optional[str] = None


class WorkOrderStatistics(BaseModel):
    total: int = 0
    by_status: dict = {}
    by_priority: dict = {}
    active: int = 0
    completed: int = 0
