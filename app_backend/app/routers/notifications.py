# app/routers/notifications.py
"""Notification API endpoints - נקודות קצה להתראות"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.core.authorization import AuthorizationService
from app.core.authorization.scope_strategies import NotificationScopeStrategy
from app.models.user import User


def _check_notification_ownership(user: User, notification) -> None:
    """Raise 403 if the notification doesn't belong to this user.

    Phase 3 Wave 3.1.4 — this helper is now a thin delegate to
    NotificationScopeStrategy. Behavior unchanged (ADMIN/SUPER_ADMIN
    bypass; everyone else must be the owner). Kept as a function so
    existing call sites and unit tests targeting it continue to work
    without churn; new code should prefer
    `AuthorizationService.authorize(... resource_type="Notification")`.
    """
    NotificationScopeStrategy().check(None, user, notification)
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationStats,
    NotificationBulkAction
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])
notification_service = NotificationService()


# Alias for frontend compatibility - /notifications/my
@router.get("/my")
def get_my_notifications(
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 50,
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's notifications."""
    return get_notifications(db, page=page, page_size=page_size,
                             unread_only=unread_only, notification_type=notification_type,
                             current_user=current_user)


# Alias for frontend compatibility - /notifications/unread-count
@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get count of unread notifications."""
    from app.models.notification import Notification
    try:
        count = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()
        return {"count": count}
    except Exception:
        return {"count": 0}


# Alias for frontend compatibility - /notifications/recent
@router.get("/recent")
def get_recent_notifications(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get recent notifications (small shortcut, not paginated)."""
    notifications = notification_service.get_user_notifications(
        db=db, user_id=current_user.id, skip=0, limit=limit
    )
    return notifications or []


@router.get("/")
def get_notifications(
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 50,
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get user notifications (paginated)."""
    from app.models.notification import Notification
    try:
        skip = (page - 1) * page_size
        notifications = notification_service.get_user_notifications(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=page_size,
            unread_only=unread_only,
            notification_type=notification_type
        )

        count_q = db.query(Notification).filter(Notification.user_id == current_user.id)
        if unread_only:
            count_q = count_q.filter(Notification.is_read == False)
        if notification_type:
            count_q = count_q.filter(Notification.notification_type == notification_type)
        total = count_q.count()

        return {
            "items": notifications or [],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except Exception:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/{notification_id}", )
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get notification by ID."""
    notification = notification_service.get_notification(db, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notification


@router.post("/", )
def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new notification.

    Wave 7.G — locked behind `notifications.manage` (ADMIN only per
    Wave 7.A migration). Even before this gate, the existing
    role-code check below ensured non-admins could only create
    notifications for themselves; we keep that defensive layer.
    """
    require_permission(current_user, "notifications.manage")
    if notification.user_id != current_user.id and not (current_user.role and current_user.role.code == "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create notifications for other users"
        )
    
    created_notification = notification_service.create_notification(db, notification)
    return created_notification


@router.put("/{notification_id}", )
def update_notification(
    notification_id: int,
    notification_update: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update notification.

    Wave 7.G — admin-only mutation. Suppliers and rank-and-file users
    don't need to PUT-edit notification rows; the few attributes they
    touch (read flag) flow through the dedicated /read endpoints.
    """
    require_permission(current_user, "notifications.manage")
    notification = notification_service.get_notification(db, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Update fields
    for field, value in notification_update.dict(exclude_unset=True).items():
        setattr(notification, field, value)
    
    db.commit()
    db.refresh(notification)
    
    return notification


def _mark_one_as_read(notification_id: int, db: Session, current_user: User):
    """Internal helper — mark a single notification as read.

    Phase 3 Wave 3.1.4 — ownership check goes through
    AuthorizationService now. Behavior identical to Wave 7.G:
      - missing notification → 404
      - non-owner non-admin → 403
      - owner → success
      - ADMIN/SUPER_ADMIN → bypass (support flow)
    """
    notification = notification_service.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    AuthorizationService(db).authorize(
        current_user,
        resource=notification,
        resource_type="Notification",
    )
    return notification_service.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )


# POST (original) + PATCH (frontend expects PATCH)
@router.post("/{notification_id}/read")
def mark_notification_as_read_post(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark notification as read (POST)."""
    return _mark_one_as_read(notification_id, db, current_user)


@router.patch("/{notification_id}/read")
def mark_notification_as_read_patch(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark notification as read (PATCH — frontend compat)."""
    return _mark_one_as_read(notification_id, db, current_user)


def _mark_all_read(db: Session, current_user: User):
    updated_count = notification_service.mark_all_as_read(db=db, user_id=current_user.id)
    return {"message": f"Marked {updated_count} notifications as read", "updated_count": updated_count}


@router.post("/read-all", response_model=dict)
def mark_all_notifications_as_read_post(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark all user notifications as read (POST)."""
    return _mark_all_read(db, current_user)


@router.patch("/read-all", response_model=dict)
def mark_all_notifications_as_read_patch(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark all user notifications as read (PATCH — frontend compat)."""
    return _mark_all_read(db, current_user)


@router.post("/bulk-action", response_model=dict)
def bulk_notification_action(
    bulk_action: NotificationBulkAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Perform bulk action on notifications.

    Wave 7.G — admin-only. The per-id user-facing actions
    (mark single read / unread) are still self-service via the
    /{id}/read endpoints below.
    """
    require_permission(current_user, "notifications.manage")
    updated_count = 0
    
    for notification_id in bulk_action.notification_ids:
        notification = notification_service.get_notification(db, notification_id)
        
        if notification and notification.user_id == current_user.id:
            if bulk_action.action == "mark_read":
                notification_service.mark_as_read(db, notification_id, current_user.id)
                updated_count += 1
            elif bulk_action.action == "mark_unread":
                notification.is_read = False
                notification.read_at = None
                db.commit()
                updated_count += 1
            elif bulk_action.action == "delete":
                notification_service.delete_notification(db, notification_id, current_user.id)
                updated_count += 1
    
    return {
        "message": f"Performed {bulk_action.action} on {updated_count} notifications",
        "updated_count": updated_count
    }


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete notification.

    Wave 7.G — admin-only. Service layer additionally scopes the delete
    to user_id, but the perm gate is the primary control.
    """
    require_permission(current_user, "notifications.manage")
    success = notification_service.delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return {"message": "Notification deleted successfully"}


@router.get("/stats/summary", response_model=NotificationStats)
def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get notification statistics."""
    stats = notification_service.get_notification_stats(db, current_user.id)
    return NotificationStats(**stats)


@router.post("/cleanup")
def cleanup_old_notifications(
    days_old: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Clean up old notifications (admin only).

    Wave 7.G — replaced the inline role-code check with the
    `notifications.manage` permission gate (admin-only assignment in
    Wave 7.A migration). Behavior identical for ADMIN; cleaner audit.
    """
    require_permission(current_user, "notifications.manage")
    
    deleted_count = notification_service.cleanup_old_notifications(db, days_old)
    
    return {
        "message": f"Cleaned up {deleted_count} old notifications",
        "deleted_count": deleted_count
    }
