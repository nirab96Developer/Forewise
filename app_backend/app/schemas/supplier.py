"""
Supplier schemas - סכמות ספקים
Pydantic models for Supplier API
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict


class SupplierType(str, Enum):
    """Supplier type enum"""
    EQUIPMENT = "equipment"
    LABOR = "labor"
    MATERIALS = "materials"
    SERVICES = "services"
    BOTH = "both"


class SupplierEquipmentStatus(str, Enum):
    """Supplier equipment availability status."""
    AVAILABLE = "available"
    BUSY = "busy"
    INACTIVE = "inactive"


class SupplierBase(BaseModel):
    """
    SupplierBase - שדות בסיסיים
    """
    name: str = Field(..., min_length=1, max_length=200, description="שם הספק")
    contact_name: Optional[str] = Field(None, max_length=100, description="שם איש קשר")
    phone: Optional[str] = Field(None, max_length=20, description="טלפון")
    email: Optional[EmailStr] = Field(None, description="אימייל")
    address: Optional[str] = Field(None, max_length=500, description="כתובת")
    supplier_type: Optional[SupplierType] = Field(None, description="סוג ספק")
    region_id: Optional[int] = Field(None, gt=0, description="מזהה מרחב")
    area_id: Optional[int] = Field(None, gt=0, description="מזהה אזור")


class SupplierCreate(SupplierBase):
    """
    SupplierCreate - יצירת ספק
    """
    code: str = Field(..., min_length=1, max_length=50, description="קוד ספק")
    tax_id: Optional[str] = Field(None, max_length=50, description="מספר עוסק מורשה")
    rating: Optional[Decimal] = Field(None, ge=0, le=5, description="דירוג (0-5)")
    priority_score: int = Field(0, description="ציון עדיפות")

    @field_validator('tax_id')
    @classmethod
    def validate_tax_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate tax ID format"""
        if v:
            v = v.strip()
            if not v:
                return None
        return v

    @field_validator('code')
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate code format"""
        if v:
            v = v.strip().upper()
            if not v:
                raise ValueError("supplier code is required")
        return v


class SupplierUpdate(BaseModel):
    """
    SupplierUpdate - עדכון ספק
    """
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    tax_id: Optional[str] = Field(None, max_length=50)
    contact_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(None, max_length=500)
    supplier_type: Optional[SupplierType] = None
    rating: Optional[Decimal] = Field(None, ge=0, le=5)
    priority_score: Optional[int] = None
    average_response_time: Optional[int] = Field(None, ge=0)
    
    # Version for optimistic locking
    version: Optional[int] = Field(None, description="גרסה נוכחית")


class SupplierResponse(SupplierBase):
    """
    SupplierResponse - תשובה ללקוח
    """
    id: int
    code: Optional[str] = None
    tax_id: Optional[str] = None
    rating: Optional[Decimal] = None
    priority_score: int = 0
    average_response_time: Optional[int] = None
    last_selected: Optional[datetime] = None
    
    # Audit
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    version: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class SupplierBrief(BaseModel):
    """
    SupplierBrief - תצוגה קצרה
    """
    id: int
    name: str
    code: Optional[str] = None
    supplier_type: Optional[str] = None
    is_active: Optional[bool] = None
    rating: Optional[Decimal] = None
    
    model_config = ConfigDict(from_attributes=True)


class SupplierList(BaseModel):
    """
    SupplierList - תשובת רשימה
    """
    items: List[SupplierResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class SupplierSearch(BaseModel):
    """
    SupplierSearch - פילטרים לחיפוש
    """
    # Free text search
    q: Optional[str] = Field(None, description="חיפוש חופשי (name, code, tax_id)")
    
    # Filters
    supplier_type: Optional[SupplierType] = Field(None, description="סוג ספק")
    is_active: Optional[bool] = Field(None, description="פעיל בלבד")
    min_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="דירוג מינימלי")
    region_id: Optional[int] = Field(None, gt=0, description="סינון לפי מרחב")
    area_id: Optional[int] = Field(None, gt=0, description="סינון לפי אזור")
    
    # Pagination
    page: int = Field(1, ge=1, description="עמוד")
    page_size: int = Field(50, ge=1, le=200, description="גודל עמוד")
    
    # Sorting
    sort_by: str = Field("name", description="מיון: name, code, rating, created_at")
    sort_desc: bool = Field(False, description="מיון יורד")
    
    # Include deleted
    include_deleted: bool = Field(False, description="כולל מחוקים")


class SupplierStatistics(BaseModel):
    """
    SupplierStatistics - סטטיסטיקות
    """
    total: int = 0
    active_count: int = 0
    by_type: dict[str, int] = {}
    average_rating: Optional[Decimal] = None
    top_rated: List[SupplierBrief] = []


class SupplierEquipmentCreate(BaseModel):
    """Attach equipment model to supplier inventory."""
    equipment_model_id: int = Field(..., gt=0, description="מזהה דגם כלי")
    license_plate: str = Field(..., min_length=1, max_length=50, description="מספר רישוי")
    status: SupplierEquipmentStatus = Field(
        SupplierEquipmentStatus.AVAILABLE, description="סטטוס זמינות"
    )
    quantity_available: Optional[int] = Field(1, ge=0, description="כמות זמינה")
    hourly_rate: Optional[Decimal] = Field(None, ge=0, description="תעריף שעתי")


class SupplierEquipmentUpdate(BaseModel):
    """Update supplier equipment inventory row."""
    status: Optional[SupplierEquipmentStatus] = Field(None, description="סטטוס זמינות")
    quantity_available: Optional[int] = Field(None, ge=0, description="כמות זמינה")
    hourly_rate: Optional[Decimal] = Field(None, ge=0, description="תעריף שעתי")


class SupplierEquipmentResponse(BaseModel):
    """Supplier equipment inventory row."""
    id: int
    supplier_id: int
    equipment_model_id: Optional[int] = None
    equipment_category_id: Optional[int] = None
    license_plate: Optional[str] = None
    status: Optional[str] = None
    quantity_available: Optional[int] = None
    hourly_rate: Optional[Decimal] = None
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
