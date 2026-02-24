# app/schemas/supplier_portal.py
"""Supplier Portal schemas - סכמות לדף נחיתה של ספקים"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class SupplierPortalResponse(BaseModel):
    """תגובה לדף נחיתה של ספק"""
    
    order_number: str = Field(..., description="מספר הזמנה")
    title: str = Field(..., description="כותרת ההזמנה")
    description: Optional[str] = Field(None, description="תיאור ההזמנה")
    equipment_type: Optional[str] = Field(None, description="סוג ציוד")
    equipment_count: int = Field(1, description="כמות ציוד")
    start_date: Optional[datetime] = Field(None, description="תאריך התחלה")
    end_date: Optional[datetime] = Field(None, description="תאריך סיום")
    estimated_hours: float = Field(0, description="שעות משוערות")
    hourly_rate: float = Field(0, description="תעריף לשעה")
    location: Optional[str] = Field(None, description="מיקום העבודה")
    contact_person: Optional[str] = Field(None, description="איש קשר")
    contact_phone: Optional[str] = Field(None, description="טלפון")
    contact_email: Optional[str] = Field(None, description="מייל")
    portal_token: str = Field(..., description="מזהה דף נחיתה")
    expires_at: datetime = Field(..., description="תאריך פג תוקף")
    is_forced: bool = Field(False, description="האם זה אילוץ")
    force_reason: Optional[str] = Field(None, description="סיבת אילוץ")
    project_name: Optional[str] = Field(None, description="שם פרויקט")
    project_code: Optional[str] = Field(None, description="קוד פרויקט")
    
    model_config = ConfigDict(from_attributes=True)


class SupplierAcceptRequest(BaseModel):
    """בקשת אישור הזמנה"""
    
    license_plate: str = Field(..., description="מספר רישוי", min_length=1, max_length=20)
    notes: Optional[str] = Field(None, description="הערות", max_length=500)


class SupplierRejectRequest(BaseModel):
    """בקשת דחיית הזמנה"""
    
    reason: str = Field(..., description="סיבת דחייה", min_length=1, max_length=200)
    notes: Optional[str] = Field(None, description="הערות", max_length=500)


class SupplierPortalStatus(BaseModel):
    """סטטוס דף נחיתה"""
    
    is_valid: bool = Field(..., description="האם הדף תקין")
    is_expired: bool = Field(..., description="האם פג תוקף")
    time_remaining: Optional[int] = Field(None, description="שניות נותרות")
    status: str = Field(..., description="סטטוס ההזמנה")




