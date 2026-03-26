"""
Project schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, model_validator


# Nested basic schemas 

class RegionBasic(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class AreaBasic(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class UserBasic(BaseModel):
    id: int
    full_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# 


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

    # Nested objects (from ORM relationships)
    region:       Optional[RegionBasic] = None
    area:         Optional[AreaBasic]   = None
    manager:      Optional[UserBasic]   = None
    accountant:   Optional[UserBasic]   = None
    area_manager: Optional[UserBasic]   = None

    # Flat name aliases (populated in /code/{code} enriched endpoint)
    region_name:  Optional[str] = None
    area_name:    Optional[str] = None
    manager_name: Optional[str] = None

    # Budget summary (populated in list endpoint)
    allocated_budget: Optional[float] = None

    # Nested location (optional, loaded when needed)
    location: Optional[LocationBrief] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def _populate_name_aliases(self) -> "ProjectResponse":
        """Auto-fill flat name fields from nested objects if not already set."""
        if self.region and not self.region_name:
            self.region_name = self.region.name
        if self.area and not self.area_name:
            self.area_name = self.area.name
        if self.manager and not self.manager_name:
            self.manager_name = self.manager.full_name
        return self


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
