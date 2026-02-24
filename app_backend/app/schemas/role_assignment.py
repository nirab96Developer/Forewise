"""
RoleAssignment schemas - סכמות הקצאת תפקידים
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Base Schemas
# ============================================================================

class RoleAssignmentBase(BaseModel):
    """שדות בסיס"""
    user_id: int
    role_id: int
    scope_type: str = Field(default="GLOBAL", max_length=50)
    scope_id: Optional[int] = None


# ============================================================================
# Create & Update
# ============================================================================

class RoleAssignmentCreate(RoleAssignmentBase):
    """הקצאת תפקיד"""
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None


class RoleAssignmentUpdate(BaseModel):
    """עדכון הקצאה"""
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


# ============================================================================
# Response Schemas
# ============================================================================

class UserBrief(BaseModel):
    """משתמש - תצוגה מקוצרת"""
    id: int
    full_name: str
    email: str
    
    model_config = ConfigDict(from_attributes=True)


class RoleBrief(BaseModel):
    """תפקיד - תצוגה מקוצרת"""
    id: int
    code: str
    name: str
    
    model_config = ConfigDict(from_attributes=True)


class RoleAssignmentResponse(RoleAssignmentBase):
    """תשובת הקצאה"""
    id: int
    assigned_by: int
    assigned_at: Optional[datetime]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    is_active: Optional[bool]
    notes: Optional[str]
    
    # Nested
    user: Optional[UserBrief] = None
    role: Optional[RoleBrief] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# List
# ============================================================================

class RoleAssignmentSearch(BaseModel):
    """פילטרים לחיפוש"""
    user_id: Optional[int] = None
    role_id: Optional[int] = None
    scope_type: Optional[str] = None
    is_active: Optional[bool] = True
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class RoleAssignmentListResponse(BaseModel):
    """תשובת רשימה"""
    items: List[RoleAssignmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

