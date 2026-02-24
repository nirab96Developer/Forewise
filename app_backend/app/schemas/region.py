"""
Region schemas
"""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class RegionBase(BaseModel):
    """Base region"""
    name: str = Field(..., max_length=200, description="שם מרחב")
    description: Optional[str] = None


class RegionCreate(RegionBase):
    """Create region"""
    code: Optional[str] = Field(None, max_length=50)
    manager_id: Optional[int] = None
    total_budget: Optional[Decimal] = Field(None, description="תקציב כולל")

    @field_validator('code')
    @classmethod
    def normalize_code(cls, v: Optional[str]) -> Optional[str]:
        """Normalize code"""
        if v:
            return v.strip().upper()
        return v


class RegionUpdate(BaseModel):
    """Update region"""
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    manager_id: Optional[int] = None
    total_budget: Optional[Decimal] = Field(None, description="תקציב כולל")
    version: Optional[int] = None


class RegionResponse(RegionBase):
    """Region response"""
    id: int
    code: Optional[str] = None
    manager_id: Optional[int] = None
    total_budget: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    is_active: Optional[bool] = True
    version: Optional[int] = 1
    
    model_config = ConfigDict(from_attributes=True)


class RegionBrief(BaseModel):
    """Brief region"""
    id: int
    name: str
    code: Optional[str] = None
    is_active: Optional[bool] = True  # Default to True if None in DB
    
    model_config = ConfigDict(from_attributes=True)


class RegionList(BaseModel):
    """List response"""
    items: List[RegionResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class RegionSearch(BaseModel):
    """Search filters"""
    q: Optional[str] = None
    is_active: Optional[bool] = None
    include_deleted: bool = Field(False)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("name")
    sort_desc: bool = Field(False)


class RegionStatistics(BaseModel):
    """Statistics"""
    total: int = 0
    active_count: int = 0
