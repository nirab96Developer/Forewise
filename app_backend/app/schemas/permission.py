"""
Permission schemas - סכמות הרשאה
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ============================================================================
# Base Schemas
# ============================================================================

class PermissionBase(BaseModel):
    """שדות בסיס"""
    code: str = Field(..., min_length=3, max_length=100)
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    resource: Optional[str] = Field(None, max_length=50)
    action: Optional[str] = Field(None, max_length=50)
    
    @field_validator('code')
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        """Validate code format: resource.action"""
        if '.' not in v:
            raise ValueError('Permission code must be in format: resource.action')
        parts = v.split('.')
        if len(parts) != 2:
            raise ValueError('Permission code must have exactly one dot')
        if not parts[0] or not parts[1]:
            raise ValueError('Both resource and action are required')
        return v.lower()


# ============================================================================
# Create & Update
# ============================================================================

class PermissionCreate(PermissionBase):
    """יצירת הרשאה"""
    pass


class PermissionUpdate(BaseModel):
    """עדכון הרשאה"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    resource: Optional[str] = Field(None, max_length=50)
    action: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


# ============================================================================
# Response Schemas
# ============================================================================

class PermissionResponse(PermissionBase):
    """תשובת הרשאה"""
    id: int
    is_active: Optional[bool]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class PermissionBrief(BaseModel):
    """הרשאה - תצוגה מקוצרת"""
    id: int
    code: str
    name: str
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# List & Search
# ============================================================================

class PermissionSearch(BaseModel):
    """פילטרים לחיפוש"""
    code: Optional[str] = None
    name: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    is_active: Optional[bool] = True
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=200, ge=1, le=500)
    sort_by: str = Field(default="code")
    sort_desc: bool = False


class PermissionListResponse(BaseModel):
    """תשובת רשימה"""
    items: List[PermissionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
