"""
BudgetItem schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class BudgetItemBase(BaseModel):
    """Base budget item"""
    item_name: str = Field(..., max_length=200, description="שם פריט")
    item_type: str = Field(..., max_length=50, description="סוג פריט")
    planned_amount: Decimal = Field(..., ge=0, description="סכום מתוכנן")


class BudgetItemCreate(BudgetItemBase):
    """Create budget item"""
    budget_id: int = Field(..., description="תקציב (חובה)")
    item_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    status: str = Field("PLANNED", description="סטטוס")
    priority: Optional[int] = None
    approved_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class BudgetItemUpdate(BaseModel):
    """Update budget item"""
    item_name: Optional[str] = Field(None, max_length=200)
    item_code: Optional[str] = None
    description: Optional[str] = None
    item_type: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    planned_amount: Optional[Decimal] = Field(None, ge=0)
    approved_amount: Optional[Decimal] = Field(None, ge=0)
    committed_amount: Optional[Decimal] = Field(None, ge=0)
    actual_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    version: Optional[int] = Field(None, description="גרסה")


class BudgetItemResponse(BudgetItemBase):
    """Budget item response"""
    id: int
    budget_id: int
    item_code: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: str
    priority: Optional[int] = None
    approved_amount: Optional[Decimal] = None
    committed_amount: Optional[Decimal] = None
    actual_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_active: bool
    version: int
    
    model_config = ConfigDict(from_attributes=True)


class BudgetItemBrief(BaseModel):
    """Brief budget item"""
    id: int
    item_name: str
    item_code: Optional[str] = None
    planned_amount: Decimal
    status: str
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class BudgetItemList(BaseModel):
    """List response"""
    items: List[BudgetItemResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class BudgetItemSearch(BaseModel):
    """Search filters"""
    q: Optional[str] = None
    budget_id: Optional[int] = Field(None, description="סינון לפי תקציב")
    item_type: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    include_deleted: bool = Field(False)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("item_name")
    sort_desc: bool = Field(False)


class BudgetItemStatistics(BaseModel):
    """Statistics"""
    total: int = 0
    total_planned: Decimal = Decimal(0)
    total_approved: Decimal = Decimal(0)
    total_actual: Decimal = Decimal(0)
    by_status: dict[str, int] = {}
