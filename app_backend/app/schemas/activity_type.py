"""
Activity Type schemas - סוגי פעולות לדיווח שעות
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ActivityTypeBase(BaseModel):
    """Base schema for activity type"""
    code: str = Field(..., max_length=50, description="Unique code")
    name: str = Field(..., max_length=100, description="Display name in Hebrew")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    is_active: bool = Field(True, description="Is active")
    sort_order: int = Field(0, description="Sort order")


class ActivityTypeCreate(ActivityTypeBase):
    """Schema for creating activity type"""
    pass


class ActivityTypeUpdate(BaseModel):
    """Schema for updating activity type"""
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ActivityTypeResponse(ActivityTypeBase):
    """Schema for activity type response"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ActivityTypeListResponse(BaseModel):
    """Schema for list of activity types"""
    activity_types: List[ActivityTypeResponse]
    total: int

