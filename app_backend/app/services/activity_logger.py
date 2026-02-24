"""
Activity Logger - Centralized activity logging helper

This module provides simple helper functions to log all workflow events
for the Personal Activity Dashboard (יומן פעילות אישי).

All logs are stored in activity_logs table and can be queried by user/entity.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.services.activity_log_service import ActivityLogService

_activity_log_service = ActivityLogService()


def _log(
    db: Session,
    activity_type: str,
    action: str,
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Internal helper to log activity."""
    try:
        _activity_log_service.log_activity(
            db=db,
            user_id=user_id,
            activity_type=activity_type,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details
        )
    except Exception as e:
        # Never fail the main operation due to logging
        import traceback
        print(f"Warning: Failed to log activity: {e}")
        traceback.print_exc()


# ============================================
# WORK ORDER ACTIVITIES
# ============================================

def log_work_order_created(
    db: Session,
    work_order_id: int,
    user_id: int,
    project_id: Optional[int] = None,
    equipment_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Log: נוצרה הזמנת עבודה"""
    log_details = {
        "project_id": project_id,
        "equipment_type": equipment_type,
        "description_he": "נוצרה הזמנת עבודה"
    }
    if details:
        log_details.update(details)
    _log(
        db=db,
        activity_type="work_order",
        action="work_order.created",
        user_id=user_id,
        entity_type="work_order",
        entity_id=work_order_id,
        details=log_details
    )


def log_work_order_sent_to_coordinator(
    db: Session,
    work_order_id: int,
    user_id: int
):
    """Log: הזמנה נשלחה למתאם ספקים"""
    _log(
        db=db,
        activity_type="work_order",
        action="work_order.sent_to_coordinator",
        user_id=user_id,
        entity_type="work_order",
        entity_id=work_order_id,
        details={"description_he": "הזמנה נשלחה למתאם ספקים"}
    )


def log_work_order_approved(
    db: Session,
    work_order_id: int,
    user_id: int,
    approved_by_id: Optional[int] = None,
    equipment_id: Optional[int] = None
):
    """Log: הזמנת עבודה אושרה"""
    _log(
        db=db,
        activity_type="work_order",
        action="work_order.approved",
        user_id=user_id,
        entity_type="work_order",
        entity_id=work_order_id,
        details={
            "approved_by_id": approved_by_id,
            "equipment_id": equipment_id,
            "description_he": "הזמנת עבודה אושרה"
        }
    )


def log_work_order_rejected(
    db: Session,
    work_order_id: int,
    user_id: int,
    rejected_by_id: Optional[int] = None,
    reason: Optional[str] = None
):
    """Log: הזמנת עבודה נדחתה"""
    _log(
        db=db,
        activity_type="work_order",
        action="work_order.rejected",
        user_id=user_id,
        entity_type="work_order",
        entity_id=work_order_id,
        details={
            "rejected_by_id": rejected_by_id,
            "reason": reason,
            "description_he": "הזמנת עבודה נדחתה"
        }
    )


def log_work_order_started(
    db: Session,
    work_order_id: int,
    user_id: int
):
    """Log: עבודה החלה"""
    _log(
        db=db,
        activity_type="work_order",
        action="work_order.started",
        user_id=user_id,
        entity_type="work_order",
        entity_id=work_order_id,
        details={"description_he": "עבודה החלה"}
    )


def log_work_order_completed(
    db: Session,
    work_order_id: int,
    user_id: int
):
    """Log: עבודה הושלמה"""
    _log(
        db=db,
        activity_type="work_order",
        action="work_order.completed",
        user_id=user_id,
        entity_type="work_order",
        entity_id=work_order_id,
        details={"description_he": "עבודה הושלמה"}
    )


def log_work_order_closed(
    db: Session,
    work_order_id: int,
    user_id: int,
    actual_hours: Optional[float] = None
):
    """Log: הזמנת עבודה נסגרה"""
    _log(
        db=db,
        activity_type="work_order",
        action="work_order.closed",
        user_id=user_id,
        entity_type="work_order",
        entity_id=work_order_id,
        details={
            "actual_hours": actual_hours,
            "description_he": "הזמנת עבודה נסגרה"
        }
    )


def log_work_order_cancelled(
    db: Session,
    work_order_id: int,
    user_id: int,
    reason: Optional[str] = None
):
    """Log: הזמנת עבודה בוטלה"""
    _log(
        db=db,
        activity_type="work_order",
        action="work_order.cancelled",
        user_id=user_id,
        entity_type="work_order",
        entity_id=work_order_id,
        details={
            "reason": reason,
            "description_he": "הזמנת עבודה בוטלה"
        }
    )


def log_work_order_sent_to_supplier(
    db: Session,
    work_order_id: int,
    user_id: int,
    supplier_id: int
):
    """Log: הזמנה נשלחה לספק"""
    _log(
        db=db,
        activity_type="work_order",
        action="work_order.sent_to_supplier",
        user_id=user_id,
        entity_type="work_order",
        entity_id=work_order_id,
        details={
            "supplier_id": supplier_id,
            "description_he": f"הזמנה נשלחה לספק (ID: {supplier_id})"
        }
    )


def log_work_order_resent_to_supplier(
    db: Session,
    work_order_id: int,
    user_id: int,
    supplier_id: int
):
    """Log: הזמנה נשלחה מחדש לספק"""
    _log(
        db=db,
        activity_type="work_order",
        action="work_order.resent_to_supplier",
        user_id=user_id,
        entity_type="work_order",
        entity_id=work_order_id,
        details={
            "supplier_id": supplier_id,
            "description_he": f"הזמנה נשלחה מחדש לספק (ID: {supplier_id})"
        }
    )


def log_work_order_supplier_changed(
    db: Session,
    work_order_id: int,
    user_id: int,
    old_supplier_id: Optional[int] = None,
    new_supplier_id: Optional[int] = None
):
    """Log: ספק שונה בהזמנה"""
    _log(
        db=db,
        activity_type="work_order",
        action="work_order.supplier_changed",
        user_id=user_id,
        entity_type="work_order",
        entity_id=work_order_id,
        details={
            "old_supplier_id": old_supplier_id,
            "new_supplier_id": new_supplier_id,
            "description_he": f"ספק שונה מ-{old_supplier_id} ל-{new_supplier_id}"
        }
    )


# ============================================
# SUPPLIER COORDINATION ACTIVITIES
# ============================================

def log_supplier_landing_page_sent(
    db: Session,
    work_order_id: int,
    user_id: int,
    supplier_id: int,
    is_fair_rotation: bool = True
):
    """Log: דף נחיתה נשלח לספק"""
    _log(
        db=db,
        activity_type="supplier_coordination",
        action="supplier.landing_page_sent",
        user_id=user_id,
        entity_type="work_order",
        entity_id=work_order_id,
        details={
            "supplier_id": supplier_id,
            "is_fair_rotation": is_fair_rotation,
            "description_he": f"דף נחיתה נשלח לספק (ID: {supplier_id})"
        }
    )


def log_supplier_timer_started(
    db: Session,
    work_order_id: int,
    user_id: int,
    supplier_id: int,
    hours: int = 3
):
    """Log: טיימר הופעל לספק"""
    _log(
        db=db,
        activity_type="supplier_coordination",
        action="supplier.timer_started",
        user_id=user_id,
        entity_type="work_order",
        entity_id=work_order_id,
        details={
            "supplier_id": supplier_id,
            "timer_hours": hours,
            "description_he": f"טיימר {hours} שעות הופעל לספק"
        }
    )


def log_supplier_timer_expired(
    db: Session,
    work_order_id: int,
    supplier_id: int,
    next_supplier_id: Optional[int] = None
):
    """Log: פג טיימר - עבר לספק הבא"""
    _log(
        db=db,
        activity_type="supplier_coordination",
        action="supplier.timer_expired",
        user_id=None,
        entity_type="work_order",
        entity_id=work_order_id,
        details={
            "supplier_id": supplier_id,
            "next_supplier_id": next_supplier_id,
            "description_he": "פג טיימר - עובר לספק הבא ברוטציה"
        }
    )


def log_supplier_confirmed(
    db: Session,
    work_order_id: int,
    supplier_id: int,
    equipment_number: Optional[str] = None
):
    """Log: ספק אישר + מספר כלי"""
    _log(
        db=db,
        activity_type="supplier_coordination",
        action="supplier.confirmed",
        user_id=None,  # Supplier action
        entity_type="work_order",
        entity_id=work_order_id,
        details={
            "supplier_id": supplier_id,
            "equipment_number": equipment_number,
            "description_he": f"ספק אישר עם מספר כלי: {equipment_number}"
        }
    )


def log_supplier_declined(
    db: Session,
    work_order_id: int,
    supplier_id: int,
    reason: Optional[str] = None
):
    """Log: ספק דחה"""
    _log(
        db=db,
        activity_type="supplier_coordination",
        action="supplier.declined",
        user_id=None,
        entity_type="work_order",
        entity_id=work_order_id,
        details={
            "supplier_id": supplier_id,
            "reason": reason,
            "description_he": "ספק דחה את ההזמנה"
        }
    )


def log_constraint_rejected(
    db: Session,
    work_order_id: int,
    user_id: int,
    supplier_id: int,
    reason: str
):
    """Log: אילוץ ספק נדחה - הוחזר למנהל עבודה"""
    _log(
        db=db,
        activity_type="supplier_coordination",
        action="supplier.constraint_rejected",
        user_id=user_id,
        entity_type="work_order",
        entity_id=work_order_id,
        details={
            "supplier_id": supplier_id,
            "reason": reason,
            "description_he": f"אילוץ ספק נדחה - הוחזר למנהל עבודה (סיבה: {reason})"
        }
    )


# ============================================
# EQUIPMENT SCAN ACTIVITIES
# ============================================

def log_equipment_scanned(
    db: Session,
    equipment_scan_id: int,
    user_id: int,
    equipment_id: int,
    scan_type: str = "check_in"
):
    """Log: ציוד נסרק"""
    _log(
        db=db,
        activity_type="equipment",
        action="equipment.scanned",
        user_id=user_id,
        entity_type="equipment_scan",
        entity_id=equipment_scan_id,
        details={
            "equipment_id": equipment_id,
            "scan_type": scan_type,
            "description_he": "ציוד נסרק בשטח"
        }
    )


def log_equipment_mismatch_detected(
    db: Session,
    equipment_scan_id: int,
    user_id: int,
    expected_number: str,
    scanned_number: str,
    is_same_type: bool = True
):
    """Log: נסרק כלי - מספר שונה"""
    mismatch_type = "אותו סוג" if is_same_type else "סוג שונה"
    _log(
        db=db,
        activity_type="equipment",
        action="equipment.mismatch_detected",
        user_id=user_id,
        entity_type="equipment_scan",
        entity_id=equipment_scan_id,
        details={
            "expected_number": expected_number,
            "scanned_number": scanned_number,
            "is_same_type": is_same_type,
            "description_he": f"נסרק כלי: מספר שונה ({mismatch_type})"
        }
    )


def log_equipment_transfer_approved(
    db: Session,
    equipment_scan_id: int,
    user_id: int,
    equipment_id: int,
    from_project_id: Optional[int] = None,
    to_project_id: Optional[int] = None
):
    """Log: מנהל עבודה אישר העברת כלי"""
    _log(
        db=db,
        activity_type="equipment",
        action="equipment.transfer_approved",
        user_id=user_id,
        entity_type="equipment_scan",
        entity_id=equipment_scan_id,
        details={
            "equipment_id": equipment_id,
            "from_project_id": from_project_id,
            "to_project_id": to_project_id,
            "description_he": "מנהל עבודה אישר העברת כלי לפרויקט"
        }
    )


def log_equipment_type_change_pending(
    db: Session,
    equipment_scan_id: int,
    user_id: int,
    expected_type: str,
    scanned_type: str
):
    """Log: ממתין אישור מנהל אזור לשינוי סוג"""
    _log(
        db=db,
        activity_type="equipment",
        action="equipment.type_change_pending",
        user_id=user_id,
        entity_type="equipment_scan",
        entity_id=equipment_scan_id,
        details={
            "expected_type": expected_type,
            "scanned_type": scanned_type,
            "description_he": "סוג כלי שונה - ממתין אישור מנהל אזור"
        }
    )


def log_equipment_type_change_approved(
    db: Session,
    equipment_scan_id: int,
    user_id: int,
    approved_by_id: int
):
    """Log: מנהל אזור אישר שינוי סוג + עודכן מחירון"""
    _log(
        db=db,
        activity_type="equipment",
        action="equipment.type_change_approved",
        user_id=user_id,
        entity_type="equipment_scan",
        entity_id=equipment_scan_id,
        details={
            "approved_by_id": approved_by_id,
            "description_he": "מנהל אזור אישר שינוי סוג + עודכן מחירון"
        }
    )


# ============================================
# WORKLOG ACTIVITIES
# ============================================

def log_worklog_created(
    db: Session,
    worklog_id: int,
    user_id: int,
    work_order_id: Optional[int] = None,
    project_id: Optional[int] = None,
    is_standard: bool = True
):
    """Log: דיווח שעות נוצר"""
    report_type = "תקן" if is_standard else "לא תקן"
    _log(
        db=db,
        activity_type="worklog",
        action="worklog.created",
        user_id=user_id,
        entity_type="worklog",
        entity_id=worklog_id,
        details={
            "work_order_id": work_order_id,
            "project_id": project_id,
            "is_standard": is_standard,
            "description_he": f"דיווח שעות נוצר ({report_type})"
        }
    )


def log_worklog_submitted(
    db: Session,
    worklog_id: int,
    user_id: int,
    project_id: int = None,
    work_order_id: int = None
):
    """Log: דיווח שעות נשלח"""
    _log(
        db=db,
        activity_type="worklog",
        action="worklog.submitted",
        user_id=user_id,
        entity_type="worklog",
        entity_id=worklog_id,
        details={
            "description_he": "דיווח שעות נשלח לאישור",
            "project_id": project_id,
            "work_order_id": work_order_id
        }
    )


def log_worklog_approved(
    db: Session,
    worklog_id: int,
    user_id: int,
    approved_by_id: int,
    project_id: int = None,
    work_order_id: int = None
):
    """Log: דיווח אושר ע"י הנה"ח אזורית"""
    _log(
        db=db,
        activity_type="worklog",
        action="worklog.approved",
        user_id=user_id,
        entity_type="worklog",
        entity_id=worklog_id,
        details={
            "approved_by_id": approved_by_id,
            "project_id": project_id,
            "work_order_id": work_order_id,
            "description_he": "דיווח אושר ע״י הנה״ח אזורית"
        }
    )


def log_worklog_rejected(
    db: Session,
    worklog_id: int,
    user_id: int,
    rejected_by_id: int,
    reason: Optional[str] = None,
    project_id: int = None,
    work_order_id: int = None
):
    """Log: דיווח נדחה"""
    _log(
        db=db,
        activity_type="worklog",
        action="worklog.rejected",
        user_id=user_id,
        entity_type="worklog",
        entity_id=worklog_id,
        details={
            "rejected_by_id": rejected_by_id,
            "reason": reason,
            "project_id": project_id,
            "work_order_id": work_order_id,
            "description_he": f"דיווח נדחה (סיבה: {reason or 'לא צוינה'})"
        }
    )


def log_worklog_assigned_to_invoice(
    db: Session,
    worklog_id: int,
    user_id: int,
    invoice_id: int
):
    """Log: דיווח שויך לחשבונית"""
    _log(
        db=db,
        activity_type="worklog",
        action="worklog.assigned_to_invoice",
        user_id=user_id,
        entity_type="worklog",
        entity_id=worklog_id,
        details={
            "invoice_id": invoice_id,
            "description_he": f"דיווח שויך לחשבונית מספר {invoice_id}"
        }
    )


# ============================================
# INVOICE ACTIVITIES
# ============================================

def log_invoice_created(
    db: Session,
    invoice_id: int,
    user_id: int,
    work_order_id: Optional[int] = None,
    supplier_id: Optional[int] = None
):
    """Log: חשבונית נוצרה"""
    _log(
        db=db,
        activity_type="invoice",
        action="invoice.created",
        user_id=user_id,
        entity_type="invoice",
        entity_id=invoice_id,
        details={
            "work_order_id": work_order_id,
            "supplier_id": supplier_id,
            "description_he": "חשבונית נוצרה"
        }
    )


def log_invoice_approved(
    db: Session,
    invoice_id: int,
    user_id: int,
    approved_by_id: int
):
    """Log: חשבונית אושרה"""
    _log(
        db=db,
        activity_type="invoice",
        action="invoice.approved",
        user_id=user_id,
        entity_type="invoice",
        entity_id=invoice_id,
        details={
            "approved_by_id": approved_by_id,
            "description_he": "חשבונית אושרה"
        }
    )


def log_invoice_sent_to_supplier(
    db: Session,
    invoice_id: int,
    user_id: int,
    supplier_id: int
):
    """Log: חשבונית נשלחה לספק"""
    _log(
        db=db,
        activity_type="invoice",
        action="invoice.sent_to_supplier",
        user_id=user_id,
        entity_type="invoice",
        entity_id=invoice_id,
        details={
            "supplier_id": supplier_id,
            "description_he": "חשבונית נשלחה לספק"
        }
    )


def log_invoice_paid(
    db: Session,
    invoice_id: int,
    user_id: int,
    amount: float,
    is_partial: bool = False
):
    """Log: תשלום בוצע"""
    payment_type = "חלקי" if is_partial else "מלא"
    _log(
        db=db,
        activity_type="invoice",
        action="invoice.paid",
        user_id=user_id,
        entity_type="invoice",
        entity_id=invoice_id,
        details={
            "amount": amount,
            "is_partial": is_partial,
            "description_he": f"תשלום {payment_type} בוצע - {amount}₪"
        }
    )


# ============================================
# USER SESSION ACTIVITIES
# ============================================

def log_user_login(
    db: Session,
    user_id: int,
    method: str = "password"
):
    """Log: משתמש נכנס למערכת"""
    _log(
        db=db,
        activity_type="auth",
        action="user.login",
        user_id=user_id,
        entity_type="user",
        entity_id=user_id,
        details={
            "method": method,
            "description_he": f"כניסה למערכת ({method})"
        }
    )


def log_user_logout(
    db: Session,
    user_id: int
):
    """Log: משתמש יצא מהמערכת"""
    _log(
        db=db,
        activity_type="auth",
        action="user.logout",
        user_id=user_id,
        entity_type="user",
        entity_id=user_id,
        details={"description_he": "יציאה מהמערכת"}
    )


def log_otp_verified(
    db: Session,
    user_id: int
):
    """Log: OTP אומת בהצלחה"""
    _log(
        db=db,
        activity_type="auth",
        action="user.otp_verified",
        user_id=user_id,
        entity_type="user",
        entity_id=user_id,
        details={"description_he": "אימות OTP בוצע בהצלחה"}
    )


# ============================================
# SUPPORT TICKET ACTIVITIES
# ============================================

def log_support_ticket_created(
    db: Session,
    ticket_id: int,
    user_id: int,
    title: str = "",
    category: str = "",
    source: str = "manual"
):
    """Log: פנייה חדשה נפתחה"""
    source_he = "מהמערכת" if source == "manual" else "מהבוט"
    _log(
        db=db,
        activity_type="support",
        action="support_ticket.created",
        user_id=user_id,
        entity_type="support_ticket",
        entity_id=ticket_id,
        details={
            "title": title,
            "category": category,
            "source": source,
            "description_he": f"פנייה חדשה נפתחה {source_he}: {title}"
        }
    )


def log_support_ticket_replied(
    db: Session,
    ticket_id: int,
    user_id: int,
    is_staff: bool = False
):
    """Log: תגובה נוספה לפנייה"""
    who = "נציג תמיכה" if is_staff else "משתמש"
    _log(
        db=db,
        activity_type="support",
        action="support_ticket.replied",
        user_id=user_id,
        entity_type="support_ticket",
        entity_id=ticket_id,
        details={
            "is_staff": is_staff,
            "description_he": f"תגובה נוספה ע״י {who}"
        }
    )


def log_support_ticket_status_changed(
    db: Session,
    ticket_id: int,
    user_id: int,
    old_status: str = "",
    new_status: str = ""
):
    """Log: סטטוס פנייה השתנה"""
    status_map = {"open": "פתוח", "in_progress": "בטיפול", "resolved": "נפתר", "closed": "סגור"}
    old_he = status_map.get(old_status, old_status)
    new_he = status_map.get(new_status, new_status)
    _log(
        db=db,
        activity_type="support",
        action="support_ticket.status_changed",
        user_id=user_id,
        entity_type="support_ticket",
        entity_id=ticket_id,
        details={
            "old_status": old_status,
            "new_status": new_status,
            "description_he": f"סטטוס פנייה שונה מ-{old_he} ל-{new_he}"
        }
    )
