"""
Equipment Category schemas - CORE with self-ref
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class EquipmentCategoryBase(BaseModel):
    """Base"""
    name: str = Field(..., max_length=200, description="שם הקטגוריה")
    code: str = Field(..., max_length=50, description="קוד קטגוריה")
    description: Optional[str] = None


class EquipmentCategoryCreate(EquipmentCategoryBase):
    """Create"""
    parent_category_id: Optional[int] = None
    requires_license: bool = False
    license_type: Optional[str] = Field(None, max_length=100)
    requires_certification: bool = False
    default_hourly_rate: Optional[float] = Field(None, ge=0)
    default_daily_rate: Optional[float] = Field(None, ge=0)
    maintenance_interval_hours: Optional[int] = Field(None, ge=0)
    maintenance_interval_days: Optional[int] = Field(None, ge=0)


class EquipmentCategoryUpdate(BaseModel):
    """Update"""
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    parent_category_id: Optional[int] = None
    requires_license: Optional[bool] = None
    license_type: Optional[str] = Field(None, max_length=100)
    requires_certification: Optional[bool] = None
    default_hourly_rate: Optional[float] = Field(None, ge=0)
    default_daily_rate: Optional[float] = Field(None, ge=0)
    maintenance_interval_hours: Optional[int] = Field(None, ge=0)
    maintenance_interval_days: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    version: Optional[int] = None


class EquipmentCategoryResponse(EquipmentCategoryBase):
    """Response"""
    id: int
    parent_category_id: Optional[int] = None
    requires_license: bool
    license_type: Optional[str] = None
    requires_certification: bool
    default_hourly_rate: Optional[float] = None
    default_daily_rate: Optional[float] = None
    maintenance_interval_hours: Optional[int] = None
    maintenance_interval_days: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    metadata_json: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class EquipmentCategoryBrief(BaseModel):
    """Brief"""
    id: int
    code: str
    name: str
    parent_category_id: Optional[int] = None
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class EquipmentCategoryList(BaseModel):
    """List response"""
    items: List[EquipmentCategoryResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class EquipmentCategorySearch(BaseModel):
    """Search filters"""
    q: Optional[str] = None
    parent_category_id: Optional[int] = None
    requires_license: Optional[bool] = None
    requires_certification: Optional[bool] = None
    is_active: Optional[bool] = None
    include_deleted: bool = Field(False)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("name")
    sort_desc: bool = Field(False)


class EquipmentCategoryStatistics(BaseModel):
    """Statistics"""
    total: int = 0
    active_count: int = 0
    root_count: int = 0  # Categories without parent
