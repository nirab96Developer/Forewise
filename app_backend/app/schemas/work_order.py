"""
WorkOrder schemas - סכמות הזמנות עבודה
Pydantic models for WorkOrder API
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict


class WorkOrderStatus(str, Enum):
    """Work order status enum"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class WorkOrderPriority(str, Enum):
    """Work order priority enum - case-insensitive"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    
    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive lookup"""
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value == value_lower:
                    return member
        return None


class WorkOrderBase(BaseModel):
    """
    WorkOrderBase - שדות בסיסיים
    """
    title: Optional[str] = Field(None, max_length=200, description="כותרת")
    description: Optional[str] = Field(None, description="תיאור")
    priority: Optional[WorkOrderPriority] = Field(WorkOrderPriority.MEDIUM, description="עדיפות")


class WorkOrderCreate(WorkOrderBase):
    """
    WorkOrderCreate - יצירת הזמנת עבודה
    """
    # Required FK
    project_id: int = Field(..., description="מזהה פרויקט (חובה)")
    
    # Optional FKs
    supplier_id: Optional[int] = Field(None, description="מזהה ספק")
    equipment_id: Optional[int] = Field(None, description="מזהה ציוד")
    requested_equipment_model_id: int = Field(..., gt=0, description="מזהה דגם כלי מבוקש (חובה)")
    location_id: Optional[int] = Field(None, description="מזהה מיקום")
    
    # Work details
    work_start_date: Optional[date] = Field(None, description="תאריך התחלה")
    work_end_date: Optional[date] = Field(None, description="תאריך סיום")
    estimated_hours: Optional[Decimal] = Field(None, ge=0, description="שעות משוערות")
    
    # Financial
    hourly_rate: Optional[Decimal] = Field(None, ge=0, description="תעריף שעתי")
    total_amount: Optional[Decimal] = Field(None, ge=0, description="סכום כולל")
    frozen_amount: Decimal = Field(0, ge=0, description="סכום מוקפא")
    
    # Status
    status: Optional[WorkOrderStatus] = Field(WorkOrderStatus.PENDING, description="סטטוס")
    
    # Notes
    constraint_reason_id: Optional[int] = Field(None, description="מזהה סיבת אילוץ ספק")
    is_forced_selection: Optional[bool] = Field(False, description="האם מדובר בבחירת ספק באילוץ")
    constraint_notes: Optional[str] = Field(None, description="הערות אילוץ")

    @field_validator('work_end_date')
    @classmethod
    def validate_end_date(cls, v: Optional[date], info) -> Optional[date]:
        """Validate end_date is after start_date"""
        if v and info.data.get('work_start_date'):
            if v < info.data['work_start_date']:
                raise ValueError("work_end_date must be after work_start_date")
        return v


class WorkOrderUpdate(BaseModel):
    """
    WorkOrderUpdate - עדכון הזמנת עבודה
    All fields optional for partial updates
    """
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    
    # FKs
    project_id: Optional[int] = None
    supplier_id: Optional[int] = None
    equipment_id: Optional[int] = None
    requested_equipment_model_id: Optional[int] = Field(None, gt=0)
    location_id: Optional[int] = None
    
    # Dates
    work_start_date: Optional[date] = None
    work_end_date: Optional[date] = None
    
    # Hours
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    actual_hours: Optional[Decimal] = Field(None, ge=0)
    
    # Financial
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    frozen_amount: Optional[Decimal] = Field(None, ge=0)
    charged_amount: Optional[Decimal] = Field(None, ge=0)
    
    # Priority & Status
    priority: Optional[WorkOrderPriority] = None
    status: Optional[WorkOrderStatus] = None
    
    # Notes
    constraint_notes: Optional[str] = None
    rejection_notes: Optional[str] = None
    
    # Version for optimistic locking
    version: Optional[int] = Field(None, description="גרסה נוכחית")


class WorkOrderResponse(WorkOrderBase):
    """
    WorkOrderResponse - תשובה ללקוח
    """
    # System fields
    id: int
    order_number: int
    
    # FKs
    project_id: Optional[int] = None
    supplier_id: Optional[int] = None
    equipment_id: Optional[int] = None
    requested_equipment_model_id: Optional[int] = Field(None, gt=0)
    location_id: Optional[int] = None
    created_by_id: Optional[int] = None
    
    # Status
    status: Optional[str] = None
    
    # Dates
    work_start_date: Optional[date] = None
    work_end_date: Optional[date] = None
    response_received_at: Optional[datetime] = None
    supplier_response_at: Optional[datetime] = None
    
    # Hours
    estimated_hours: Optional[Decimal] = None
    actual_hours: Optional[Decimal] = None
    
    # Financial
    hourly_rate: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    frozen_amount: Decimal = 0
    charged_amount: Decimal = 0
    remaining_frozen_amount: Optional[Decimal] = None
    
    # Constraints/Rejection
    constraint_reason_id: Optional[int] = None
    constraint_notes: Optional[str] = None
    rejection_reason_id: Optional[int] = None
    rejection_notes: Optional[str] = None
    is_forced_selection: Optional[bool] = None
    
    # Portal
    portal_token: Optional[str] = None
    portal_expiry: Optional[datetime] = None
    
    # Audit
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    version: int
    
    model_config = ConfigDict(from_attributes=True)


class WorkOrderBrief(BaseModel):
    """
    WorkOrderBrief - תצוגה קצרה
    For lists, dropdowns
    """
    id: int
    order_number: int
    title: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    project_id: Optional[int] = None
    supplier_id: Optional[int] = None
    work_start_date: Optional[date] = None
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)


class WorkOrderList(BaseModel):
    """
    WorkOrderList - תשובת רשימה
    """
    items: List[WorkOrderResponse]
    total: int
    page: int = 1
    page_size: int = 20  # Reduced for better performance with high latency DB
    total_pages: int = 1


class WorkOrderSearch(BaseModel):
    """
    WorkOrderSearch - פילטרים לחיפוש
    """
    # Free text
    q: Optional[str] = Field(None, description="חיפוש חופשי")
    
    # Filters
    project_id: Optional[int] = Field(None, description="פרויקט")
    supplier_id: Optional[int] = Field(None, description="ספק")
    equipment_id: Optional[int] = Field(None, description="ציוד")
    requested_equipment_model_id: Optional[int] = Field(None, gt=0, description="דגם כלי מבוקש")
    location_id: Optional[int] = Field(None, description="מיקום")
    status: Optional[WorkOrderStatus] = Field(None, description="סטטוס")
    priority: Optional[WorkOrderPriority] = Field(None, description="עדיפות")
    created_by_id: Optional[int] = Field(None, description="נוצר על ידי")
    area_id: Optional[int] = Field(None, description="אזור (RBAC)")
    
    # Date ranges
    start_date_from: Optional[date] = Field(None, description="תאריך התחלה מ-")
    start_date_to: Optional[date] = Field(None, description="תאריך התחלה עד")
    
    # Flags
    is_active: Optional[bool] = Field(None, description="פעיל בלבד")
    include_deleted: bool = Field(False, description="כולל מחוקים")
    
    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    
    # Sorting
    sort_by: str = Field("created_at", description="מיון: order_number, created_at, status, priority")
    sort_desc: bool = Field(True, description="מיון יורד")


class WorkOrderStatusUpdate(BaseModel):
    """
    WorkOrderStatusUpdate - עדכון סטטוס
    """
    status: WorkOrderStatus = Field(..., description="סטטוס חדש")
    notes: Optional[str] = Field(None, max_length=500, description="הערות")
    version: Optional[int] = Field(None, description="גרסה (optimistic locking)")


class WorkOrderApproveRequest(BaseModel):
    """
    WorkOrderApproveRequest - אישור הזמנה
    """
    equipment_id: Optional[int] = Field(None, description="ציוד מאושר")
    supplier_id: Optional[int] = Field(None, description="ספק מאושר")
    hourly_rate: Optional[Decimal] = Field(None, ge=0, description="תעריף")
    notes: Optional[str] = Field(None, description="הערות")
    version: Optional[int] = Field(None, description="גרסה")


class WorkOrderRejectRequest(BaseModel):
    """
    WorkOrderRejectRequest - דחיית הזמנה
    """
    rejection_reason_id: int = Field(..., description="סיבת דחייה (חובה)")
    rejection_notes: Optional[str] = Field(None, max_length=500, description="הערות")
    version: Optional[int] = Field(None, description="גרסה")


class WorkOrderStatistics(BaseModel):
    """
    WorkOrderStatistics - סטטיסטיקות
    """
    total: int = 0
    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    pending_count: int = 0
    approved_count: int = 0
    active_count: int = 0
    completed_count: int = 0
    total_frozen_amount: Decimal = Decimal(0)
    total_charged_amount: Decimal = Decimal(0)
