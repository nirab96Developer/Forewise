# app/schemas/activity_log.py
"""Activity log schemas - Complete alignment with model."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ActivityType(str, Enum):
    """Activity type enum - matches model."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    TWO_FA_ENABLED = "2fa_enabled"
    TWO_FA_DISABLED = "2fa_disabled"

    # CRUD Operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

    # Business Actions
    APPROVE = "approve"
    REJECT = "reject"
    SUBMIT = "submit"
    CANCEL = "cancel"
    ASSIGN = "assign"
    UNASSIGN = "unassign"

    # Data Operations
    EXPORT = "export"
    IMPORT = "import"
    DOWNLOAD = "download"
    UPLOAD = "upload"

    # System
    API_CALL = "api_call"
    ERROR = "error"
    WARNING = "warning"


class ActivityLogBase(BaseModel):
    """Base activity log schema."""
    user_id: Optional[int] = Field(None, description="User who performed the activity")
    # Changed to str for flexibility
    activity_type: Optional[str] = Field(None, description="Type of activity")
    action: str = Field(..., max_length=200, description="Action performed")
    description: Optional[str] = Field(None, description="Detailed description")

    # Entity reference
    entity_type: Optional[str] = Field(None, max_length=50)
    entity_id: Optional[int] = None
    entity_name: Optional[str] = Field(None, max_length=200)

    # Category for role-based filtering
    category: Optional[str] = Field(
        "system", 
        max_length=50,
        description="Activity category: operational, financial, management, system"
    )

    # Request context
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)
    endpoint: Optional[str] = Field(None, max_length=200)
    method: Optional[str] = Field(None, max_length=10)
    status_code: Optional[int] = Field(None, ge=100, le=599)


class ActivityLogCreate(ActivityLogBase):
    """Create activity log entry."""
    metadata: Optional[Dict[str, Any]] = None
    changes: Optional[Dict[str, Any]] = None


class ActivityLogUpdate(BaseModel):
    """Update activity log - rarely used."""
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = Field(None, ge=100, le=599)


ACTION_LABELS_HE = {
    # Authentication
    "login": "כניסה למערכת",
    "logout": "יציאה מהמערכת",
    "login_failed": "כניסה נכשלה",
    "password_change": "שינוי סיסמה",
    "password_reset": "איפוס סיסמה",
    "user_login": "כניסה למערכת",
    "user_logout": "יציאה מהמערכת",
    "2fa verification successful": "כניסה למערכת",
    "2fa_verified": "כניסה למערכת",
    # Generic CRUD
    "create": "יצירה",
    "update": "עדכון",
    "delete": "מחיקה",
    "approve": "אישור",
    "reject": "דחייה",
    "submit": "הגשה",
    "cancel": "ביטול",
    "assign": "הקצאה",
    # Work orders — underscore
    "work_order_created": "הזמנת עבודה נוצרה",
    "work_order_approved": "הזמנת עבודה אושרה",
    "work_order_rejected": "הזמנת עבודה נדחתה",
    "work_order_sent": "הזמנה נשלחה לספק",
    "work_order_completed": "הזמנה הושלמה",
    "work_order_deleted": "הזמנת עבודה נמחקה",
    # Work orders — dot notation
    "work_order.created": "הזמנת עבודה נוצרה",
    "work_order.approved": "הזמנת עבודה אושרה",
    "work_order.rejected": "הזמנת עבודה נדחתה",
    "work_order.deleted": "הזמנת עבודה נמחקה",
    "work_order.started": "הזמנת עבודה החלה",
    "work_order.closed": "הזמנת עבודה נסגרה",
    "work_order.cancelled": "הזמנת עבודה בוטלה",
    "work_order.sent_to_supplier": "הזמנה נשלחה לספק",
    "work_order.resent_to_supplier": "הזמנה נשלחה מחדש לספק",
    "work_order.supplier_changed": "ספק הוחלף בהזמנה",
    # Worklogs — underscore
    "worklog_created": "דיווח שעות חדש",
    "worklog_approved": "דיווח שעות אושר",
    "worklog_rejected": "דיווח שעות נדחה",
    # Worklogs — dot notation
    "worklog.created": "דיווח שעות נוצר",
    "worklog.approved": "דיווח שעות אושר",
    "worklog.rejected": "דיווח שעות נדחה",
    "worklog.submitted": "דיווח שעות הוגש",
    "worklog.assigned_to_invoice": "דיווח שויך לחשבונית",
    # Suppliers
    "supplier_added": "ספק חדש נוסף",
    "supplier_forced": "ספק אולץ ידנית",
    "supplier.landing_page_sent": "דף נחיתה נשלח לספק",
    "supplier.timer_started": "טיימר ספק הופעל",
    "supplier.timer_expired": "זמן תגובת ספק פג",
    "supplier.confirmed": "ספק אישר הזמנה",
    "supplier.declined": "ספק דחה הזמנה",
    "supplier.constraint_rejected": "ספק נדחה באילוץ",
    # Equipment
    "equipment_assigned": "ציוד הוקצה",
    "equipment_removed": "ציוד הוסר מפרויקט",
    "equipment.scanned": "ציוד נסרק",
    "equipment.mismatch_detected": "אי-התאמה בציוד",
    "equipment.released": "ציוד שוחרר",
    "equipment.transfer_approved": "העברת ציוד אושרה",
    # Invoices
    "invoice_created": "חשבונית נוצרה",
    "invoice_approved": "חשבונית אושרה",
    "invoice.created": "חשבונית נוצרה",
    "invoice.approved": "חשבונית אושרה",
    "invoice.sent_to_supplier": "חשבונית נשלחה לספק",
    "invoice.paid": "חשבונית שולמה",
    # Budget
    "budget_updated": "תקציב עודכן",
    "budget_freeze": "תקציב הוקפא",
    "budget_release": "תקציב שוחרר",
    "balance_release": "יתרה שוחררה",
    # Projects / Users
    "project_created": "פרויקט חדש נוצר",
    "user_created": "משתמש חדש נוסף",
    # Misc
    "note": "הערה נוספה",
}

ENTITY_LABELS_HE = {
    "work_order": "הזמנת עבודה",
    "worklog": "דיווח שעות",
    "project": "פרויקט",
    "invoice": "חשבונית",
    "user": "משתמש",
    "supplier": "ספק",
    "equipment": "ציוד",
    "budget": "תקציב",
}


class ActivityLogResponse(ActivityLogBase):
    """Activity log response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # From relationships
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    # Hebrew display
    display_name_he: Optional[str] = None
    entity_name_he: Optional[str] = None

    # JSON fields - stored as string in DB, parsed here
    custom_metadata: Optional[Any] = None
    changes: Optional[Any] = None

    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore'
    )

    @model_validator(mode='after')
    def populate_hebrew(self):
        action_key = (self.action or '').lower()
        activity_key = (self.activity_type or '').lower()
        self.display_name_he = (
            ACTION_LABELS_HE.get(action_key)
            or ACTION_LABELS_HE.get(action_key.replace('.', '_'))
            or ACTION_LABELS_HE.get(action_key.replace('_', '.'))
            or ACTION_LABELS_HE.get(activity_key)
            or ACTION_LABELS_HE.get(activity_key.replace('.', '_'))
            or self.action or ''
        )
        self.entity_name_he = ENTITY_LABELS_HE.get((self.entity_type or '').lower(), self.entity_type or '')
        return self


class ActivityLogFilter(BaseModel):
    """Filter activity logs."""
    user_id: Optional[int] = None
    user_ids: Optional[List[int]] = None
    activity_type: Optional[ActivityType] = None
    activity_types: Optional[List[ActivityType]] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    ip_address: Optional[str] = None
    search: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    has_errors: Optional[bool] = None


class ActivityStatistics(BaseModel):
    """Activity statistics."""
    total_activities: int = 0
    unique_users: int = 0

    # Breakdowns
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_action: Dict[str, int] = Field(default_factory=dict)
    by_entity_type: Dict[str, int] = Field(default_factory=dict)
    by_hour: Dict[int, int] = Field(default_factory=dict)
    by_day: Dict[str, int] = Field(default_factory=dict)

    # Top lists
    most_active_users: List[Dict[str, Any]] = Field(default_factory=list)
    most_common_actions: List[Dict[str, Any]] = Field(default_factory=list)
    recent_errors: List[Dict[str, Any]] = Field(default_factory=list)

    # Time range
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class UserActivitySummary(BaseModel):
    """User activity summary."""
    user_id: int
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    total_activities: int = 0
    first_activity: Optional[datetime] = None
    last_activity: Optional[datetime] = None

    # Activity breakdown
    activities_by_type: Dict[str, int] = Field(default_factory=dict)
    activities_by_day: Dict[str, int] = Field(default_factory=dict)

    # Recent activity
    recent_activities: List[Dict[str, Any]] = Field(default_factory=list)

    # Login info
    total_logins: int = 0
    failed_logins: int = 0
    last_login: Optional[datetime] = None
    last_login_ip: Optional[str] = None


class SuspiciousActivity(BaseModel):
    """Suspicious activity alert."""
    type: str  # multiple_failed_logins, unusual_hours, mass_export, etc.
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    count: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class ActivityExport(BaseModel):
    """Export configuration."""
    format: str = Field("csv", pattern="^(csv|excel|json)$")
    filters: Optional[ActivityLogFilter] = None
    include_user_details: bool = True
    include_metadata: bool = False
