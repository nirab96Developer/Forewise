"""
Worklog schemas
"""

from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class WorklogBase(BaseModel):
    """Base worklog schema"""
    report_date: Optional[date] = Field(None, description="תאריך דיווח")
    work_date: Optional[date] = Field(None, description="תאריך עבודה (alias)")
    work_hours: Optional[Decimal] = Field(None, ge=0, description="שעות עבודה")
    activity_description: Optional[str] = Field(None, description="תיאור פעילות")
    description: Optional[str] = Field(None, description="תיאור (alias)")
    notes: Optional[str] = None

    model_config = ConfigDict(extra='allow')


class WorklogCreate(WorklogBase):
    """Create worklog — accepts frontend field names"""
    work_order_id: Optional[int] = Field(None, description="הזמנת עבודה")
    
    user_id: Optional[int] = Field(None, description="משתמש")
    project_id: Optional[int] = Field(None, description="פרויקט")
    activity_type_id: Optional[int] = Field(None, description="סוג פעילות")
    
    equipment_id: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_hours: Optional[Decimal] = Field(None, ge=0)
    total_hours: Optional[Decimal] = Field(None, ge=0, description="סה\"כ שעות")
    billable_hours: Optional[Decimal] = Field(None, ge=0)
    work_type: Optional[str] = None
    equipment_scanned: Optional[bool] = None
    
    report_type: Optional[str] = Field("standard", description="standard/manual/storage")
    is_standard: bool = Field(True, description="דיווח תקן")
    
    # Frontend sends these — accepted but handled separately
    activity_type: Optional[str] = Field(None, description="סוג פעילות (שם)")
    activity: Optional[str] = Field(None, description="פעילות")
    non_standard_reason: Optional[str] = None
    non_standard_notes: Optional[str] = None
    includes_guard: Optional[bool] = None
    segments: Optional[list] = None
    supplier_id: Optional[int] = None


class WorklogUpdate(BaseModel):
    """Update worklog"""
    report_date: Optional[date] = None
    work_hours: Optional[Decimal] = Field(None, ge=0)
    break_hours: Optional[Decimal] = Field(None, ge=0)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    activity_description: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class WorklogResponse(WorklogBase):
    """Worklog response"""
    id: int
    report_number: int
    report_type: str
    
    # FKs
    work_order_id: Optional[int] = None
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    area_id: Optional[int] = None
    equipment_id: Optional[int] = None
    activity_type_id: Optional[int] = None
    status: Optional[str] = None
    
    # Times
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_hours: Optional[Decimal] = None
    total_hours: Optional[Decimal] = None
    
    # Financial
    hourly_rate_snapshot: Optional[Decimal] = None
    cost_before_vat: Optional[Decimal] = None
    cost_with_vat: Optional[Decimal] = None
    vat_rate: Decimal = Decimal('0.17')
    
    # Approval
    approved_by_user_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    
    # Audit
    created_at: datetime
    updated_at: datetime
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)


class WorklogBrief(BaseModel):
    """Brief worklog for lists"""
    id: int
    report_number: int
    report_date: date
    work_hours: Decimal
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    status: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class WorklogList(BaseModel):
    """Paginated list"""
    items: List[WorklogResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class WorklogSearch(BaseModel):
    """Search filters"""
    q: Optional[str] = Field(None, description="חיפוש")
    work_order_id: Optional[int] = None
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    area_id: Optional[int] = None
    equipment_id: Optional[int] = None
    status: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    is_active: Optional[bool] = None
    
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("report_date", description="created_at, report_date, report_number")
    sort_desc: bool = Field(True)


class WorklogStatistics(BaseModel):
    """Statistics"""
    total: int = 0
    total_hours: Decimal = Decimal(0)
    total_cost: Decimal = Decimal(0)
    by_status: dict[str, int] = {}
    by_project: dict[str, Decimal] = {}
