"""
Project schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ProjectBase(BaseModel):
    """Base"""
    name: str = Field(..., max_length=200, description="שם הפרויקט")
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Create"""
    manager_id: int = Field(..., description="מנהל פרויקט")
    region_id: int = Field(..., description="אזור")
    area_id: int = Field(..., description="אזור משני")
    location_id: int = Field(..., description="מיקום")
    budget_id: Optional[int] = None


class ProjectUpdate(BaseModel):
    """Update"""
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    manager_id: Optional[int] = None
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    location_id: Optional[int] = None
    budget_id: Optional[int] = None
    is_active: Optional[bool] = None
    version: Optional[int] = None


class LocationBrief(BaseModel):
    """Location brief for embedding in project"""
    id: int
    code: str
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    metadata_json: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(ProjectBase):
    """Response"""
    id: int
    manager_id: Optional[int] = None
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    location_id: Optional[int] = None
    budget_id: Optional[int] = None
    is_active: Optional[bool] = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    version: Optional[int] = 1
    
    # Nested location (optional, loaded when needed)
    location: Optional[LocationBrief] = None
    
    model_config = ConfigDict(from_attributes=True)


class ProjectBrief(BaseModel):
    """Brief"""
    id: int
    code: Optional[str] = None
    name: str
    region_id: Optional[int] = None
    is_active: Optional[bool] = True
    
    model_config = ConfigDict(from_attributes=True)


class ProjectList(BaseModel):
    """List response"""
    items: List[ProjectResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class ProjectSearch(BaseModel):
    """Search filters"""
    q: Optional[str] = None
    manager_id: Optional[int] = None
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    location_id: Optional[int] = None
    is_active: Optional[bool] = None
    include_deleted: bool = Field(False)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("name")
    sort_desc: bool = Field(False)


class ProjectStatistics(BaseModel):
    """Statistics"""
    total: int = 0
    active_count: int = 0
