"""
User schemas - סכמות משתמש
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


# ============================================================================
# Base Schemas
# ============================================================================

class UserBase(BaseModel):
    """שדות בסיס משותפים"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)


# ============================================================================
# Create Schema
# ============================================================================

class UserCreate(UserBase):
    """יצירת משתמש חדש"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    role_id: Optional[int] = None
    department_id: Optional[int] = None
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    scope_level: Optional[str] = None
    two_factor_enabled: bool = False
    is_active: Optional[bool] = True
    project_ids: Optional[List[int]] = Field(default=[], description="רשימת פרויקטים לשיוך אוטומטי")


# ============================================================================
# Update Schema
# ============================================================================

class UserUpdate(BaseModel):
    """עדכון משתמש - הכל אופציונלי"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    role_id: Optional[int] = None
    department_id: Optional[int] = None
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    scope_level: Optional[str] = None
    is_active: Optional[bool] = None
    two_factor_enabled: Optional[bool] = None
    must_change_password: Optional[bool] = None


# ============================================================================
# Response Schemas
# ============================================================================

class RoleBrief(BaseModel):
    """תפקיד - תצוגה מקוצרת"""
    id: int
    code: str
    name: str
    
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """תשובת משתמש מלאה"""
    id: int
    email: str  # Use str instead of EmailStr to allow .local domains
    full_name: Optional[str] = None
    phone: Optional[str] = None
    username: Optional[str] = None
    role_id: Optional[int] = None
    department_id: Optional[int] = None
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    scope_level: Optional[str] = None
    status: Optional[str] = "ACTIVE"
    is_active: Optional[bool] = True
    is_locked: Optional[bool] = False
    two_factor_enabled: Optional[bool] = False
    must_change_password: Optional[bool] = False
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Nested
    role: Optional[RoleBrief] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserBrief(BaseModel):
    """משתמש - תצוגה מקוצרת (לרשימות/dropdown)"""
    id: int
    full_name: str
    email: str
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# List & Search Schemas
# ============================================================================

class UserSearch(BaseModel):
    """פילטרים לחיפוש משתמשים"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    department_id: Optional[int] = None
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    is_active: Optional[bool] = True  # Default: only active
    status: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    sort_by: str = Field(default="created_at")
    sort_desc: bool = True


class UserListResponse(BaseModel):
    """תשובת רשימת משתמשים"""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Special Schemas
# ============================================================================

class UserPasswordChange(BaseModel):
    """החלפת סיסמה"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UserLock(BaseModel):
    """נעילת משתמש"""
    locked_until: Optional[datetime] = None  # None = forever
    reason: Optional[str] = None
