# app/routers/notifications.py
"""Notification API endpoints - נקודות קצה להתראות"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationStats,
    NotificationBulkAction
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])
notification_service = NotificationService()


# Alias for frontend compatibility - /notifications/my
@router.get("/my", )
def get_my_notifications(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's notifications."""
    return get_notifications(db, skip, limit, unread_only, notification_type, current_user)


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
@router.get("/recent", )
def get_recent_notifications(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get recent notifications."""
    return get_notifications(db, 0, limit, False, None, current_user)


@router.get("/", )
def get_notifications(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get user notifications."""
    notifications = notification_service.get_user_notifications(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
        notification_type=notification_type
    )
    return notifications


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
    """Create new notification."""
    # Only allow creating notifications for the current user or if user is admin
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
    """Update notification."""
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


@router.post("/{notification_id}/read", )
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark notification as read."""
    notification = notification_service.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return notification


@router.post("/read-all", response_model=dict)
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark all user notifications as read."""
    updated_count = notification_service.mark_all_as_read(
        db=db,
        user_id=current_user.id
    )
    
    return {
        "message": f"Marked {updated_count} notifications as read",
        "updated_count": updated_count
    }


@router.post("/bulk-action", response_model=dict)
def bulk_notification_action(
    bulk_action: NotificationBulkAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Perform bulk action on notifications."""
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
    """Delete notification."""
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
    """Clean up old notifications (admin only)."""
    if not (current_user.role and current_user.role.code == "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    deleted_count = notification_service.cleanup_old_notifications(db, days_old)
    
    return {
        "message": f"Cleaned up {deleted_count} old notifications",
        "deleted_count": deleted_count
    }
