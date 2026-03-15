# app/schemas/notification.py
"""Notification schemas - סכמות להתראות"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class NotificationType(str, Enum):
    """Notification type enum."""
    SYSTEM = "system"
    PROJECT = "project"
    WORK_ORDER = "work_order"
    WORK_ORDER_APPROVED = "work_order_approved"
    WORK_ORDER_REJECTED = "work_order_rejected"
    SUPPLIER_RESPONSE = "supplier_response"
    BUDGET_ALERT = "budget_alert"
    EQUIPMENT_MAINTENANCE = "equipment_maintenance"
    EQUIPMENT_LOW_HOURS = "EQUIPMENT_LOW_HOURS"
    INVOICE = "invoice"
    INVOICE_PENDING = "INVOICE_PENDING"
    WORK_LOG = "work_log"
    WORKLOG_PENDING = "WORKLOG_PENDING"
    WORKLOG_APPROVED = "WORKLOG_APPROVED"
    SUPPORT_TICKET = "support_ticket"


class NotificationPriority(str, Enum):
    """Notification priority enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationBase(BaseModel):
    """Base notification schema."""
    
    user_id: int = Field(..., description="מזהה משתמש")
    title: str = Field(..., description="כותרת ההתראה")
    message: str = Field(..., description="תוכן ההתראה")
    notification_type: str = Field(..., description="סוג ההתראה")
    priority: str = Field("medium", description="עדיפות")
    channel: Optional[str] = Field(None, description="ערוץ שליחה")
    entity_type: Optional[str] = Field(None, description="סוג ישות")
    entity_id: Optional[int] = Field(None, description="מזהה ישות")
    data: Optional[str] = Field(None, description="נתונים JSON")
    action_url: Optional[str] = Field(None, description="קישור לפעולה")
    link: Optional[str] = Field(None, description="קישור")
    project_id: Optional[int] = Field(None, description="מזהה פרויקט")
    work_order_id: Optional[int] = Field(None, description="מזהה הזמנת עבודה")
    supplier_id: Optional[int] = Field(None, description="מזהה ספק")
    metadata: Optional[Dict[str, Any]] = Field(None, description="נתונים נוספים")


class NotificationCreate(NotificationBase):
    """Create notification schema."""
    pass


class NotificationUpdate(BaseModel):
    """Update notification schema."""
    
    is_read: Optional[bool] = None


class NotificationResponse(BaseModel):
    """Notification response schema."""
    
    id: int
    user_id: Optional[int] = None
    title: str
    message: str
    type: Optional[str] = None  # DB column name is 'type' not 'notification_type'
    notification_type: Optional[str] = None
    priority: Optional[str] = None
    is_read: bool = Field(False, description="האם נקרא")
    read_at: Optional[datetime] = Field(None, description="תאריך קריאה")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Optional fields from DB
    channel: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    action_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    data: Optional[str] = None  # DB stores as text, not dict
    
    # Relationships
    project_name: Optional[str] = None
    work_order_number: Optional[str] = None
    supplier_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class NotificationStats(BaseModel):
    """Notification statistics."""
    
    total: int = Field(..., description="סה\"כ התראות")
    unread: int = Field(..., description="התראות לא נקראו")
    critical: int = Field(..., description="התראות קריטיות")
    read_percentage: float = Field(..., description="אחוז קריאה")


class NotificationBulkAction(BaseModel):
    """Bulk notification action."""
    
    notification_ids: List[int] = Field(..., description="מזהי התראות")
    action: str = Field(..., description="פעולה לביצוע")  # "mark_read", "delete", "mark_unread"