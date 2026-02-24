"""
Location schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class LocationBase(BaseModel):
    """Base"""
    code: str = Field(..., max_length=50, description="קוד מיקום")
    name: str = Field(..., max_length=200, description="שם המיקום")
    description: Optional[str] = None
    area_id: int = Field(..., description="אזור")


class LocationCreate(LocationBase):
    """Create"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = Field(None, max_length=500)


class LocationUpdate(BaseModel):
    """Update"""
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    area_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    version: Optional[int] = None


class LocationResponse(LocationBase):
    """Response"""
    id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    version: Optional[int] = 1
    metadata_json: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class LocationBrief(BaseModel):
    """Brief"""
    id: int
    code: str
    name: str
    area_id: int
    is_active: Optional[bool] = True
    
    model_config = ConfigDict(from_attributes=True)


class LocationList(BaseModel):
    """List response"""
    items: List[LocationResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class LocationSearch(BaseModel):
    """Search filters"""
    q: Optional[str] = None
    area_id: Optional[int] = None
    is_active: Optional[bool] = None
    include_deleted: bool = Field(False)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("name")
    sort_desc: bool = Field(False)


class LocationStatistics(BaseModel):
    """Statistics"""
    total: int = 0
    active_count: int = 0
