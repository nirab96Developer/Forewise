"""
Equipment Type schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class EquipmentTypeBase(BaseModel):
    """Base equipment type"""
    code: str = Field(..., max_length=50, description="קוד סוג ציוד")
    name: str = Field(..., max_length=200, description="שם סוג הציוד")
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)


class EquipmentTypeCreate(EquipmentTypeBase):
    """Create equipment type"""
    default_hourly_rate: Decimal = Field(Decimal('0'), ge=0)
    default_daily_rate: Optional[Decimal] = Field(None, ge=0)
    default_storage_hourly_rate: Decimal = Field(Decimal('0'), ge=0)
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    overnight_rate: Optional[Decimal] = Field(None, ge=0)
    night_guard: Optional[bool] = False
    category_id: Optional[int] = None
    category_group: Optional[str] = Field(None, max_length=50)
    sort_order: int = Field(0, ge=0)


class EquipmentTypeUpdate(BaseModel):
    """Update equipment type"""
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    category_id: Optional[int] = None
    category_group: Optional[str] = Field(None, max_length=50)
    default_hourly_rate: Optional[Decimal] = Field(None, ge=0)
    default_daily_rate: Optional[Decimal] = Field(None, ge=0)
    default_storage_hourly_rate: Optional[Decimal] = Field(None, ge=0)
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    overnight_rate: Optional[Decimal] = Field(None, ge=0)
    night_guard: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class EquipmentTypeResponse(EquipmentTypeBase):
    """Equipment type response"""
    id: int
    default_hourly_rate: Optional[Decimal] = Decimal('0')
    default_daily_rate: Optional[Decimal] = None
    default_storage_hourly_rate: Optional[Decimal] = Decimal('0')
    hourly_rate: Optional[Decimal] = None
    overnight_rate: Optional[Decimal] = None
    night_guard: Optional[bool] = False
    category_id: Optional[int] = None
    category_group: Optional[str] = None
    sort_order: Optional[int] = 0
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EquipmentTypeBrief(BaseModel):
    """Brief equipment type"""
    id: int
    code: str
    name: str
    default_hourly_rate: Decimal
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class EquipmentTypeList(BaseModel):
    """List response"""
    items: List[EquipmentTypeResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class EquipmentTypeSearch(BaseModel):
    """Search filters"""
    q: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("sort_order")
    sort_desc: bool = Field(False)


class EquipmentTypeStatistics(BaseModel):
    """Statistics"""
    total: int = 0
    active_count: int = 0
