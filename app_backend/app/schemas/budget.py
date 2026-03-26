"""
Budget schemas
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class BudgetBase(BaseModel):
    """Base budget schema"""
    name: Optional[str] = Field(None, max_length=200, description="שם תקציב")
    description: Optional[str] = Field(None, description="תיאור")
    budget_type: Optional[str] = Field(None, max_length=50, description="סוג תקציב")
    total_amount: Decimal = Field(default=Decimal("0"), ge=0, description="סכום כולל")


class BudgetCreate(BudgetBase):
    """Create budget"""
    code: Optional[str] = Field(None, max_length=50)
    parent_budget_id: Optional[int] = Field(None, description="תקציב אב")
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    project_id: Optional[int] = None
    fiscal_year: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = Field("DRAFT", description="סטטוס")
    notes: Optional[str] = None


class BudgetUpdate(BaseModel):
    """Update budget"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    code: Optional[str] = Field(None, max_length=50)
    budget_type: Optional[str] = None
    status: Optional[str] = None
    total_amount: Optional[Decimal] = Field(None, ge=0)
    allocated_amount: Optional[Decimal] = Field(None, ge=0)
    spent_amount: Optional[Decimal] = Field(None, ge=0)
    committed_amount: Optional[Decimal] = Field(None, ge=0)
    parent_budget_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    version: Optional[int] = Field(None, description="גרסה")


class BudgetResponse(BudgetBase):
    """Budget response"""
    id: int
    code: Optional[str] = None
    status: Optional[str] = "DRAFT"
    parent_budget_id: Optional[int] = None
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    project_id: Optional[int] = None
    created_by: Optional[int] = None
    allocated_amount: Optional[Decimal] = None
    spent_amount: Optional[Decimal] = None
    committed_amount: Optional[Decimal] = None
    fiscal_year: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_active: bool
    version: int
    
    model_config = ConfigDict(from_attributes=True)


class BudgetBrief(BaseModel):
    """Brief budget"""
    id: int
    name: Optional[str] = None
    code: Optional[str] = None
    budget_type: Optional[str] = None
    total_amount: Decimal = Decimal("0")
    status: Optional[str] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class BudgetList(BaseModel):
    """List response"""
    items: List[BudgetResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class BudgetSearch(BaseModel):
    """Search filters"""
    q: Optional[str] = Field(None, description="חיפוש")
    budget_type: Optional[str] = None
    status: Optional[str] = None
    parent_budget_id: Optional[int] = None
    fiscal_year: Optional[int] = None
    is_active: Optional[bool] = None
    include_deleted: bool = Field(False)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)
    sort_by: str = Field("name")
    sort_desc: bool = Field(False)


class BudgetStatistics(BaseModel):
    """Statistics"""
    total: int = 0
    total_amount: Decimal = Decimal(0)
    total_spent: Decimal = Decimal(0)
    total_allocated: Decimal = Decimal(0)
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
