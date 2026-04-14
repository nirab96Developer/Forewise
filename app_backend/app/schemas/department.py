"""
Department schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class DepartmentBase(BaseModel):
    """Base department"""
    code: str = Field(..., max_length=50, description="קוד מחלקה")
    name: str = Field(..., max_length=200, description="שם המחלקה")
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    """Create department"""
    manager_id: Optional[int] = None
    parent_department_id: Optional[int] = None
    metadata_json: Optional[str] = None


class DepartmentUpdate(BaseModel):
    """Update department"""
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    manager_id: Optional[int] = None
    parent_department_id: Optional[int] = None
    metadata_json: Optional[str] = None
    version: Optional[int] = None


class DepartmentResponse(DepartmentBase):
    """Department response"""
    id: int
    manager_id: Optional[int] = None
    parent_department_id: Optional[int] = None
    metadata_json: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_active: Optional[bool] = True
    version: Optional[int] = 1
    
    model_config = ConfigDict(from_attributes=True)


class DepartmentBrief(BaseModel):
    """Brief department"""
    id: int
    code: str
    name: str
    parent_department_id: Optional[int] = None
    is_active: Optional[bool] = True
    
    model_config = ConfigDict(from_attributes=True)


class DepartmentList(BaseModel):
    """List response"""
    items: List[DepartmentResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class DepartmentSearch(BaseModel):
    """Search filters"""
    q: Optional[str] = None
    parent_department_id: Optional[int] = None
    is_active: Optional[bool] = None
    include_deleted: bool = Field(False)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("name")
    sort_desc: bool = Field(False)


class DepartmentStatistics(BaseModel):
    """Statistics"""
    total: int = 0
    active_count: int = 0
    root_count: int = 0  # Departments without parent
