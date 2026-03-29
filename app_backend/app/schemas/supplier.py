"""
Supplier schemas
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, EmailStr


class SupplierBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    contact_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None


class SupplierCreate(SupplierBase):
    status: Optional[str] = Field(None, max_length=50)
    tax_id: Optional[str] = Field(None, max_length=50)
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    active_area_ids: List[int] = []
    active_region_ids: List[int] = []


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    contact_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    id: int
    status: Optional[str] = None
    is_active: Optional[bool] = None
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    rating: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    region_name: Optional[str] = None
    area_name: Optional[str] = None
    equipment_count: int = 0
    total_assignments: int = 0
    total_skips: int = 0
    active_area_ids: List[int] = []
    active_region_ids: List[int] = []

    model_config = ConfigDict(from_attributes=True)


class SupplierBrief(BaseModel):
    id: int
    code: str
    name: str
    model_config = ConfigDict(from_attributes=True)


class SupplierSearch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = True
    q: Optional[str] = None               # free-text search
    supplier_type: Optional[str] = None
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    min_rating: Optional[float] = None
    sort_by: str = 'name'
    sort_desc: bool = False
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)


class SupplierListResponse(BaseModel):
    items: List[SupplierResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SupplierStatistics(BaseModel):
    total: int = 0
    active: int = 0
    by_region: dict = {}
    by_area: dict = {}
    avg_rating: float = 0.0


class SupplierEquipmentBase(BaseModel):
    equipment_category_id: Optional[int] = None
    equipment_model_id: Optional[int] = None
    license_plate: Optional[str] = None
    status: Optional[str] = "available"
    quantity_available: Optional[int] = 1
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = True


class SupplierEquipmentCreate(SupplierEquipmentBase):
    pass


class SupplierEquipmentUpdate(SupplierEquipmentBase):
    pass


class SupplierEquipmentResponse(SupplierEquipmentBase):
    id: int
    supplier_id: int
    model_config = ConfigDict(from_attributes=True)
