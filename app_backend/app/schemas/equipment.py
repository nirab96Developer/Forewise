"""
Equipment schemas - סכמות ציוד
Pydantic models for Equipment API
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict


class EquipmentStatus(str, Enum):
    """Equipment status enum - supports both lowercase and uppercase values"""
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"
    ACTIVE = "active"  # Legacy status
    # Uppercase aliases for DB compatibility
    AVAILABLE_UPPER = "AVAILABLE"
    IN_USE_UPPER = "IN_USE"
    MAINTENANCE_UPPER = "MAINTENANCE"
    RETIRED_UPPER = "RETIRED"
    ACTIVE_UPPER = "ACTIVE"


class EquipmentFuelType(str, Enum):
    """Fuel type enum for vehicles"""
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"


class EquipmentBase(BaseModel):
    """
    EquipmentBase - שדות בסיסיים
    Used for shared fields between Create/Update/Response
    """
    name: str = Field(..., min_length=1, max_length=255, description="שם הציוד")
    description: Optional[str] = Field(None, description="תיאור")
    equipment_type: Optional[str] = Field(None, max_length=100, description="סוג ציוד (legacy)")
    manufacturer: Optional[str] = Field(None, max_length=100, description="יצרן")
    model: Optional[str] = Field(None, max_length=100, description="דגם")
    license_plate: Optional[str] = Field(None, max_length=20, description="מספר רישוי")
    qr_code: Optional[str] = Field(None, max_length=100, description="קוד QR")
    fuel_type: Optional[str] = Field(None, description="סוג דלק")
    status: Optional[EquipmentStatus] = Field(EquipmentStatus.AVAILABLE, description="סטטוס")


class EquipmentCreate(EquipmentBase):
    """
    EquipmentCreate - יצירת ציוד חדש
    All required fields for creating equipment
    """
    # Type & Category (FKs)
    type_id: Optional[int] = Field(None, description="מזהה סוג ציוד")
    category_id: Optional[int] = Field(None, description="מזהה קטגוריה")
    supplier_id: Optional[int] = Field(None, description="מזהה ספק")
    
    # Optional fields
    code: Optional[str] = Field(None, max_length=50, description="קוד ציוד")
    location_id: Optional[int] = Field(None, description="מיקום")
    
    # Financial
    purchase_date: Optional[date] = Field(None, description="תאריך רכישה")
    purchase_price: Optional[Decimal] = Field(None, ge=0, description="מחיר רכישה")
    hourly_rate: Optional[Decimal] = Field(None, ge=0, description="תעריף שעתי")
    daily_rate: Optional[Decimal] = Field(None, ge=0, description="תעריף יומי")
    storage_hourly_rate: Optional[Decimal] = Field(None, ge=0, description="תעריף אחסון שעתי")
    
    # Maintenance
    last_maintenance: Optional[date] = Field(None, description="תחזוקה אחרונה")
    next_maintenance: Optional[date] = Field(None, description="תחזוקה הבאה")
    
    # Metadata
    metadata_json: Optional[str] = Field(None, description="מטא-דאטה (JSON)")

    @field_validator('license_plate')
    @classmethod
    def validate_license_plate(cls, v: Optional[str]) -> Optional[str]:
        """Validate license plate format"""
        if v:
            v = v.strip().upper()
            if not v:
                return None
        return v

    @field_validator('qr_code')
    @classmethod
    def validate_qr_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate QR code format"""
        if v:
            v = v.strip()
            if not v:
                return None
        return v


class EquipmentUpdate(BaseModel):
    """
    EquipmentUpdate - עדכון ציוד
    All fields optional for partial updates
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    equipment_type: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    license_plate: Optional[str] = Field(None, max_length=20)
    qr_code: Optional[str] = Field(None, max_length=100)
    fuel_type: Optional[str] = None
    status: Optional[EquipmentStatus] = None
    
    # FKs
    type_id: Optional[int] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    location_id: Optional[int] = None
    
    # Financial
    purchase_date: Optional[date] = None
    purchase_price: Optional[Decimal] = Field(None, ge=0)
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    daily_rate: Optional[Decimal] = Field(None, ge=0)
    storage_hourly_rate: Optional[Decimal] = Field(None, ge=0)
    
    # Maintenance
    last_maintenance: Optional[date] = None
    next_maintenance: Optional[date] = None
    
    # Metadata
    metadata_json: Optional[str] = None
    
    # Version for optimistic locking
    version: Optional[int] = Field(None, description="גרסה נוכחית (optimistic locking)")


class EquipmentResponse(EquipmentBase):
    """
    EquipmentResponse - תשובה ללקוח
    Full equipment data returned from API
    """
    # System fields
    id: int
    code: Optional[str] = None
    
    # FKs
    type_id: Optional[int] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    location_id: Optional[int] = None
    assigned_to_user_id: Optional[int] = None
    assigned_project_id: Optional[int] = None
    
    # Financial
    purchase_date: Optional[date] = None
    purchase_price: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    daily_rate: Optional[Decimal] = None
    storage_hourly_rate: Optional[Decimal] = None
    
    # Maintenance
    last_maintenance: Optional[date] = None
    next_maintenance: Optional[date] = None
    
    # Audit
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    is_active: bool
    version: Optional[int] = None
    
    # Computed/Related fields
    supplier_name: Optional[str] = None
    category_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class EquipmentBrief(BaseModel):
    """
    EquipmentBrief - תצוגה קצרה
    For lists, dropdowns, autocomplete
    """
    id: int
    name: str
    code: Optional[str] = None
    license_plate: Optional[str] = None
    status: Optional[str] = None
    type_id: Optional[int] = None
    category_id: Optional[int] = None
    is_active: bool
    
    # Computed display name
    display_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class EquipmentList(BaseModel):
    """
    EquipmentList - תשובת רשימה
    Paginated list response
    """
    items: List[EquipmentResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1


class EquipmentSearch(BaseModel):
    """
    EquipmentSearch - פילטרים לחיפוש
    Query parameters for filtering equipment list
    """
    # Free text search
    q: Optional[str] = Field(None, description="חיפוש חופשי (name, code, license_plate)")
    
    # Filters
    type_id: Optional[int] = Field(None, description="סוג ציוד")
    category_id: Optional[int] = Field(None, description="קטגוריה")
    supplier_id: Optional[int] = Field(None, description="ספק")
    status: Optional[EquipmentStatus] = Field(None, description="סטטוס")
    location_id: Optional[int] = Field(None, description="מיקום")
    assigned_project_id: Optional[int] = Field(None, description="פרויקט משוייך")
    is_active: Optional[bool] = Field(None, description="פעיל בלבד")
    include_deleted: bool = Field(False, description="כולל מחוקים")
    
    # Maintenance filters
    needs_maintenance: Optional[bool] = Field(None, description="צריך תחזוקה")
    
    # Pagination
    page: int = Field(1, ge=1, description="עמוד")
    page_size: int = Field(50, ge=1, le=1000, description="גודל עמוד")
    
    # Sorting
    sort_by: str = Field("name", description="מיון לפי: name, code, created_at, status")
    sort_desc: bool = Field(False, description="מיון יורד")


class EquipmentAssignRequest(BaseModel):
    """
    EquipmentAssignRequest - בקשת הקצאה
    For assigning equipment to project/location
    """
    equipment_id: int = Field(..., description="מזהה ציוד")
    
    # Assignment target (one of these should be provided)
    project_id: Optional[int] = Field(None, description="פרויקט יעד")
    location_id: Optional[int] = Field(None, description="מיקום יעד")
    user_id: Optional[int] = Field(None, description="משתמש יעד")
    
    # Time constraints
    start_date: Optional[datetime] = Field(None, description="תאריך התחלה")
    end_date: Optional[datetime] = Field(None, description="תאריך סיום")
    
    # Notes
    notes: Optional[str] = Field(None, max_length=500, description="הערות")

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate end_date is after start_date"""
        if v and info.data.get('start_date'):
            if v < info.data['start_date']:
                raise ValueError("end_date must be after start_date")
        return v


class EquipmentStatistics(BaseModel):
    """
    EquipmentStatistics - סטטיסטיקות
    Dashboard/reporting statistics
    """
    total: int = 0
    available: int = 0
    in_use: int = 0
    maintenance: int = 0
    retired: int = 0
    needs_maintenance: int = 0
    by_type: dict[str, int] = {}
    by_category: dict[str, int] = {}
    total_value: Optional[Decimal] = None
