"""
Role schemas - סכמות תפקיד
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Base Schemas
# ============================================================================

class RoleBase(BaseModel):
    """שדות בסיס"""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


# ============================================================================
# Create & Update
# ============================================================================

class RoleCreate(RoleBase):
    """יצירת תפקיד"""
    display_order: int = Field(default=99, ge=0, le=999)


class RoleUpdate(BaseModel):
    """עדכון תפקיד"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0, le=999)
    is_active: Optional[bool] = None


# ============================================================================
# Response Schemas
# ============================================================================

class PermissionBrief(BaseModel):
    """הרשאה - תצוגה מקוצרת"""
    id: int
    code: str
    name: str
    
    model_config = ConfigDict(from_attributes=True)


class RoleResponse(RoleBase):
    """תשובת תפקיד"""
    id: int
    display_order: int
    is_active: Optional[bool]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    # Nested
    permissions: Optional[List[PermissionBrief]] = None
    user_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class RoleBrief(BaseModel):
    """תפקיד - תצוגה מקוצרת"""
    id: int
    code: str
    name: str
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# List & Search
# ============================================================================

class RoleSearch(BaseModel):
    """פילטרים לחיפוש"""
    code: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = True
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    sort_by: str = Field(default="display_order")
    sort_desc: bool = False


class RoleListResponse(BaseModel):
    """תשובת רשימה"""
    items: List[RoleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Permission Assignment
# ============================================================================

class RolePermissionAssign(BaseModel):
    """הקצאת הרשאה לתפקיד"""
    permission_id: int
