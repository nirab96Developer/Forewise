"""
Area schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class AreaBase(BaseModel):
    """Base area"""
    name: str = Field(..., max_length=200, description="שם אזור משני")
    region_id: Optional[int] = Field(None, description="אזור ראשי")
    description: Optional[str] = None


class AreaCreate(AreaBase):
    """Create area"""
    code: Optional[str] = Field(None, max_length=50)
    manager_id: Optional[int] = None
    total_area_hectares: Optional[Decimal] = None


class AreaUpdate(BaseModel):
    """Update area"""
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    region_id: Optional[int] = None
    manager_id: Optional[int] = None
    description: Optional[str] = None
    total_area_hectares: Optional[Decimal] = None
    version: Optional[int] = None


class AreaResponse(AreaBase):
    """Area response"""
    id: int
    code: Optional[str] = None
    manager_id: Optional[int] = None
    total_area_hectares: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_active: bool
    version: int
    
    model_config = ConfigDict(from_attributes=True)


class AreaBrief(BaseModel):
    """Brief area"""
    id: int
    name: str
    code: Optional[str] = None
    region_id: Optional[int] = None
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class AreaList(BaseModel):
    """List response"""
    items: List[AreaResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class AreaSearch(BaseModel):
    """Search filters"""
    q: Optional[str] = None
    region_id: Optional[int] = None
    is_active: Optional[bool] = None
    include_deleted: bool = Field(False)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("name")
    sort_desc: bool = Field(False)


class AreaStatistics(BaseModel):
    """Statistics"""
    total: int = 0
    active_count: int = 0
