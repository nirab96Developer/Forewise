"""
Supplier Constraint Reason schemas - Multilingual LOOKUP
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class SupplierConstraintReasonBase(BaseModel):
    """Base"""
    code: str = Field(..., max_length=50, description="קוד סיבה")
    name_he: str = Field(..., max_length=200, description="שם בעברית")
    name_en: Optional[str] = Field(None, max_length=200, description="שם באנגלית")
    description: Optional[str] = None
    category: str = Field(..., max_length=100, description="קטגוריה")


class SupplierConstraintReasonCreate(SupplierConstraintReasonBase):
    """Create"""
    requires_additional_text: bool = False
    requires_approval: bool = False
    display_order: int = Field(0, ge=0)


class SupplierConstraintReasonUpdate(BaseModel):
    """Update"""
    code: Optional[str] = Field(None, max_length=50)
    name_he: Optional[str] = Field(None, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    requires_additional_text: Optional[bool] = None
    requires_approval: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    version: Optional[int] = None


class SupplierConstraintReasonResponse(SupplierConstraintReasonBase):
    """Response"""
    id: int
    requires_additional_text: bool
    requires_approval: bool
    display_order: int
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    version: int
    metadata_json: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class SupplierConstraintReasonBrief(BaseModel):
    """Brief"""
    id: int
    code: str
    name_he: str
    name_en: Optional[str] = None
    category: str
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class SupplierConstraintReasonList(BaseModel):
    """List response"""
    items: List[SupplierConstraintReasonResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class SupplierConstraintReasonSearch(BaseModel):
    """Search filters"""
    q: Optional[str] = None
    category: Optional[str] = None
    requires_approval: Optional[bool] = None
    is_active: Optional[bool] = None
    include_deleted: bool = Field(False)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    sort_by: str = Field("display_order")
    sort_desc: bool = Field(False)


class SupplierConstraintReasonStatistics(BaseModel):
    """Statistics"""
    total: int = 0
    active_count: int = 0
    by_category: dict = Field(default_factory=dict)
