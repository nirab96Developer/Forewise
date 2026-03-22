# app/services/notification_service.py
"""Notification service - שירות התראות בזמן אמת"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationPriority,
)

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _ws_send(user_id: int, payload: dict):
    """Best-effort WebSocket push — never raises."""
    try:
        from app.routers.websocket import manager  # local import avoids circular
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.call_soon_threadsafe(
                lambda: asyncio.ensure_future(manager.send_to_user(user_id, payload))
            )
    except Exception:
        pass


def notify(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "work_order",
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    priority: str = "medium",
    action_url: Optional[str] = None,
) -> Optional[Notification]:
    """
    Simple, direct notification creator.
    Used internally from all routers — no Pydantic schema required.
    """
    try:
        n = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            entity_type=entity_type,
            entity_id=entity_id,
            action_url=action_url,
            is_read=False,
            is_sent=False,
        )
        db.add(n)
        db.commit()
        db.refresh(n)

        _ws_send(user_id, {
            "type": "notification",
            "data": {
                "id": n.id,
                "title": title,
                "message": message,
                "notification_type": notification_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action_url": action_url,
                "priority": priority,
                "is_read": False,
                "created_at": n.created_at.isoformat() if n.created_at else datetime.utcnow().isoformat(),
            },
        })
        return n
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        log.warning(f"notify() failed [user={user_id} title={title!r}]: {e}")
        return None


def _find_users_by_role(db: Session, role_code: str, area_id: Optional[int] = None, region_id: Optional[int] = None) -> List[User]:
    """Find active users with a given role, optionally filtered by area/region."""
    from app.models.role import Role
    q = (
        db.query(User)
        .join(Role, Role.id == User.role_id)
        .filter(Role.code == role_code, User.is_active == True)
    )
    if area_id is not None:
        q = q.filter(User.area_id == area_id)
    elif region_id is not None:
        q = q.filter(User.region_id == region_id)
    return q.all()


# ─────────────────────────────────────────────────────────────
# Business-event notification helpers
# ─────────────────────────────────────────────────────────────

def notify_work_order_created(db: Session, work_order):
    """
    הזמנה חדשה נוצרה → התראה ל-ORDER_COORDINATOR של האזור.
    """
    try:
        from app.models.project import Project
        area_id = None
        try:
            if work_order.project:
                area_id = work_order.project.area_id
        except Exception:
            pass
        if area_id is None and work_order.project_id:
            proj = db.query(Project).filter(Project.id == work_order.project_id).first()
            if proj:
                area_id = proj.area_id
        coordinators = _find_users_by_role(db, "ORDER_COORDINATOR", area_id=area_id)
        wo_num = getattr(work_order, 'order_number', work_order.id)
        for coord in coordinators:
            notify(
                db, coord.id,
                title="הזמנת עבודה חדשה ממתינה לתיאום",
                message=f"הזמנה #{wo_num} נוצרה וממתינה לשליחה לספק",
                notification_type="work_order",
                entity_type="work_order",
                entity_id=work_order.id,
                action_url=f"/work-orders/{work_order.id}",
            )
    except Exception as e:
        log.warning(f"notify_work_order_created failed: {e}")


def notify_supplier_accepted(db: Session, work_order):
    """
    ספק אישר הזמנה → התראה ל-ORDER_COORDINATOR.
    """
    try:
        from app.models.project import Project
        area_id = None
        # Try to get area_id from project (handle lazy-load / None)
        try:
            if work_order.project:
                area_id = work_order.project.area_id
        except Exception:
            pass
        if area_id is None and work_order.project_id:
            proj = db.query(Project).filter(Project.id == work_order.project_id).first()
            if proj:
                area_id = proj.area_id

        coordinators = _find_users_by_role(db, "ORDER_COORDINATOR", area_id=area_id)
        wo_num = getattr(work_order, 'order_number', work_order.id)
        try:
            supplier_name = work_order.supplier.name if work_order.supplier else "ספק"
        except Exception:
            supplier_name = "ספק"
        for coord in coordinators:
            notify(
                db, coord.id,
                title="ספק אישר הזמנה — ממתין לאישור מתאם",
                message=f"הזמנה #{wo_num}: {supplier_name} אישר. נדרש אישורך.",
                notification_type="supplier_response",
                entity_type="work_order",
                entity_id=work_order.id,
                priority="high",
                action_url=f"/work-orders/{work_order.id}",
            )
    except Exception as e:
        log.warning(f"notify_supplier_accepted failed: {e}")


def notify_work_order_approved(db: Session, work_order):
    """
    ORDER_COORDINATOR אישר הזמנה → התראה ל-WORK_MANAGER שיצר.
    """
    try:
        creator_id = getattr(work_order, 'created_by_id', None)
        wo_num = getattr(work_order, 'order_number', work_order.id)
        if creator_id:
            notify(
                db, creator_id,
                title="הזמנת עבודה אושרה",
                message=f"הזמנה #{wo_num} אושרה על ידי מתאם ההזמנות",
                notification_type="work_order",
                entity_type="work_order",
                entity_id=work_order.id,
                action_url=f"/work-orders/{work_order.id}",
            )
    except Exception as e:
        log.warning(f"notify_work_order_approved failed: {e}")


def notify_work_order_rejected(db: Session, work_order, reason: str = ""):
    """
    הזמנה נדחתה → התראה ל-WORK_MANAGER שיצר.
    """
    try:
        creator_id = getattr(work_order, 'created_by_id', None)
        wo_num = getattr(work_order, 'order_number', work_order.id)
        if creator_id:
            msg = f"הזמנה #{wo_num} נדחתה"
            if reason:
                msg += f": {reason}"
            notify(
                db, creator_id,
                title="הזמנת עבודה נדחתה",
                message=msg,
                notification_type="work_order",
                entity_type="work_order",
                entity_id=work_order.id,
                priority="high",
                action_url=f"/work-orders/{work_order.id}",
            )
    except Exception as e:
        log.warning(f"notify_work_order_rejected failed: {e}")


def notify_worklog_created(db: Session, worklog):
    """
    דיווח שעות נוצר → התראה ל-AREA_MANAGER של האזור לאישור.
    """
    try:
        from app.models.project import Project
        area_id = getattr(worklog, 'area_id', None)
        if area_id is None:
            try:
                if worklog.project:
                    area_id = worklog.project.area_id
            except Exception:
                pass
        if area_id is None and getattr(worklog, 'project_id', None):
            proj = db.query(Project).filter(Project.id == worklog.project_id).first()
            if proj:
                area_id = proj.area_id

        area_managers = _find_users_by_role(db, "AREA_MANAGER", area_id=area_id)
        try:
            reporter_name = worklog.user.full_name if worklog.user else "עובד"
        except Exception:
            reporter_name = f"משתמש #{getattr(worklog, 'user_id', '?')}"
        report_date_obj = getattr(worklog, 'report_date', None) or getattr(worklog, 'work_date', None)
        report_date = report_date_obj.strftime("%d/%m/%Y") if report_date_obj else ""
        for mgr in area_managers:
            notify(
                db, mgr.id,
                title="דיווח שעות ממתין לאישור",
                message=f"דיווח של {reporter_name} מתאריך {report_date} ממתין לאישורך",
                notification_type="work_log",
                entity_type="worklog",
                entity_id=worklog.id,
                action_url=f"/work-logs/{worklog.id}",
            )
    except Exception as e:
        log.warning(f"notify_worklog_created failed: {e}")


def notify_worklog_approved(db: Session, worklog):
    """
    דיווח שעות אושר → התראה ל-WORK_MANAGER שדיווח.
    """
    try:
        reporter_id = getattr(worklog, 'user_id', None)
        report_date_obj = getattr(worklog, 'report_date', None) or getattr(worklog, 'work_date', None)
        report_date = report_date_obj.strftime("%d/%m/%Y") if report_date_obj else ""
        if reporter_id:
            notify(
                db, reporter_id,
                title="דיווח שעות אושר ✓",
                message=f"דיווח השעות שלך מתאריך {report_date} אושר על ידי מנהל האזור",
                notification_type="work_log",
                entity_type="worklog",
                entity_id=worklog.id,
                action_url=f"/work-logs/{worklog.id}",
            )
    except Exception as e:
        log.warning(f"notify_worklog_approved failed: {e}")


def notify_worklog_rejected(db: Session, worklog, reason: str = ""):
    """
    דיווח שעות נדחה → התראה ל-WORK_MANAGER שדיווח.
    """
    try:
        reporter_id = getattr(worklog, 'user_id', None)
        report_date_obj = getattr(worklog, 'report_date', None) or getattr(worklog, 'work_date', None)
        report_date = report_date_obj.strftime("%d/%m/%Y") if report_date_obj else ""
        if reporter_id:
            msg = f"דיווח השעות שלך מתאריך {report_date} נדחה"
            if reason:
                msg += f": {reason}"
            notify(
                db, reporter_id,
                title="דיווח שעות נדחה",
                message=msg,
                notification_type="work_log",
                entity_type="worklog",
                entity_id=worklog.id,
                priority="high",
                action_url=f"/work-logs/{worklog.id}",
            )
    except Exception as e:
        log.warning(f"notify_worklog_rejected failed: {e}")


def notify_invoice_created(db: Session, invoice):
    """
    חשבונית חדשה → התראה לכל מנהלות החשבונות.
    """
    try:
        from app.models.project import Project
        try:
            project_name = invoice.project.name if invoice.project else "פרויקט"
        except Exception:
            proj = db.query(Project).filter(Project.id == invoice.project_id).first() if invoice.project_id else None
            project_name = proj.name if proj else "פרויקט"
        amount = float(invoice.total_amount or 0)
        accountants = _find_users_by_role(db, "ACCOUNTANT")
        for acct in accountants:
            notify(
                db, acct.id,
                title="חשבונית חדשה לאישור",
                message=f"חשבונית {invoice.invoice_number} עבור {project_name} (₪{amount:,.0f}) ממתינה לאישורך",
                notification_type="invoice",
                entity_type="invoice",
                entity_id=invoice.id,
                priority="high",
                action_url=f"/invoices/{invoice.id}",
            )
    except Exception as e:
        log.warning(f"notify_invoice_created failed: {e}")


def notify_invoice_approved(db: Session, invoice):
    """
    חשבונית אושרה → התראה ל-AREA_MANAGER.
    """
    try:
        from app.models.project import Project
        area_id = None
        project_name = "פרויקט"
        try:
            if invoice.project:
                area_id = invoice.project.area_id
                project_name = invoice.project.name
        except Exception:
            pass
        if area_id is None and getattr(invoice, 'project_id', None):
            proj = db.query(Project).filter(Project.id == invoice.project_id).first()
            if proj:
                area_id = proj.area_id
                project_name = proj.name

        amount = float(invoice.total_amount or 0)
        if area_id:
            for mgr in _find_users_by_role(db, "AREA_MANAGER", area_id=area_id):
                notify(
                    db, mgr.id,
                    title="חשבונית אושרה",
                    message=f"חשבונית {invoice.invoice_number} עבור {project_name} (₪{amount:,.0f}) אושרה",
                    notification_type="invoice",
                    entity_type="invoice",
                    entity_id=invoice.id,
                    action_url=f"/invoices/{invoice.id}",
                )
    except Exception as e:
        log.warning(f"notify_invoice_approved failed: {e}")


# ─────────────────────────────────────────────────────────────
# NotificationService class (used by notifications router)
# ─────────────────────────────────────────────────────────────

class NotificationService:
    """Service for notification CRUD operations."""

    def get_notification(self, db: Session, notification_id: int) -> Optional[Notification]:
        return db.query(Notification).filter(Notification.id == notification_id).first()

    def get_user_notifications(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
    ) -> List[Notification]:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        if notification_type:
            query = query.filter(Notification.notification_type == notification_type)
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    def get_unread_count(self, db: Session, user_id: int) -> int:
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .count()
        )

    def create_notification(self, db: Session, notification: NotificationCreate) -> Notification:
        """Create notification from Pydantic schema (used by admin endpoint)."""
        return notify(
            db,
            user_id=notification.user_id,
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type.value if hasattr(notification.notification_type, 'value') else str(notification.notification_type),
            entity_id=getattr(notification, 'work_order_id', None) or getattr(notification, 'project_id', None),
            entity_type="work_order" if getattr(notification, 'work_order_id', None) else "project",
        )

    def mark_as_read(self, db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
        n = db.query(Notification).filter(
            Notification.id == notification_id, Notification.user_id == user_id
        ).first()
        if n:
            n.is_read = True
            n.read_at = datetime.utcnow()
            db.commit()
            db.refresh(n)
        return n

    def mark_all_as_read(self, db: Session, user_id: int) -> int:
        count = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .update({"is_read": True, "read_at": datetime.utcnow()})
        )
        db.commit()
        return count

    def delete_notification(self, db: Session, notification_id: int, user_id: int) -> bool:
        n = db.query(Notification).filter(
            Notification.id == notification_id, Notification.user_id == user_id
        ).first()
        if n:
            db.delete(n)
            db.commit()
            return True
        return False

    def get_notification_stats(self, db: Session, user_id: int) -> Dict[str, Any]:
        total = db.query(Notification).filter(Notification.user_id == user_id).count()
        unread = db.query(Notification).filter(
            Notification.user_id == user_id, Notification.is_read == False
        ).count()
        critical = db.query(Notification).filter(
            Notification.user_id == user_id, Notification.is_read == False,
            Notification.notification_type.in_(["budget_alert"])
        ).count()
        return {
            "total": total,
            "unread": unread,
            "critical": critical,
            "read_percentage": ((total - unread) / total * 100) if total > 0 else 0,
        }

    def cleanup_old_notifications(self, db: Session, days_old: int = 30) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days_old)
        count = (
            db.query(Notification)
            .filter(Notification.created_at < cutoff, Notification.is_read == True)
            .delete()
        )
        db.commit()
        return count

    # Legacy system notification (kept for compat)
    def create_system_notification(self, db: Session, title: str, message: str,
                                   priority: str = "medium", target_users: Optional[List[int]] = None):
        if target_users:
            for uid in target_users:
                notify(db, uid, title=title, message=message, notification_type="system")
        else:
            for user in db.query(User).filter(User.is_active == True).all():
                notify(db, user.id, title=title, message=message, notification_type="system")


notification_service = NotificationService()
