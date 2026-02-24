# app/services/notification_service.py
"""Notification service - שירות התראות בזמן אמת"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.notification import Notification
from app.models.user import User
from app.models.project import Project
from app.models.work_order import WorkOrder
from app.models.supplier import Supplier
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationType,
    NotificationPriority
)


class NotificationService:
    """Service for notification operations."""

    def get_notification(self, db: Session, notification_id: int) -> Optional[Notification]:
        """Get notification by ID."""
        return (
            db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )

    def get_user_notifications(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
        notification_type: Optional[str] = None
    ) -> List[Notification]:
        """Get user notifications."""
        query = (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
        )

        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        if notification_type:
            query = query.filter(Notification.notification_type == notification_type)

        return (
            query.order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_notification(
        self,
        db: Session,
        notification: NotificationCreate
    ) -> Notification:
        """Create new notification."""
        db_notification = Notification(
            user_id=notification.user_id,
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type,
            priority=notification.priority,
            channel=notification.channel,
            entity_type=notification.entity_type,
            entity_id=notification.entity_id,
            data=notification.data,
            action_url=notification.action_url,
            expires_at=notification.expires_at,
            is_read=False
        )

        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)

        # Send real-time notification via WebSocket
        self._send_realtime_notification(db_notification)

        return db_notification

    def mark_as_read(
        self,
        db: Session,
        notification_id: int,
        user_id: int
    ) -> Optional[Notification]:
        """Mark notification as read."""
        notification = (
            db.query(Notification)
            .filter(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
            .first()
        )

        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.commit()
            db.refresh(notification)

        return notification

    def mark_all_as_read(
        self,
        db: Session,
        user_id: int
    ) -> int:
        """Mark all user notifications as read."""
        updated_count = (
            db.query(Notification)
            .filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                )
            )
            .update({
                "is_read": True,
                "read_at": datetime.utcnow()
            })
        )

        db.commit()
        return updated_count

    def delete_notification(
        self,
        db: Session,
        notification_id: int,
        user_id: int
    ) -> bool:
        """Delete notification (soft delete)."""
        notification = (
            db.query(Notification)
            .filter(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
            .first()
        )

        if notification:
            # Soft delete by marking as read
            notification.is_read = True
            db.commit()
            return True

        return False

    def create_work_order_notification(
        self,
        db: Session,
        work_order: WorkOrder,
        notification_type: str,
        message: str
    ):
        """Create work order related notification."""
        # Get project manager
        if work_order.project and work_order.project.manager_id:
            notification = NotificationCreate(
                user_id=work_order.project.manager_id,
                title=f"הזמנת עבודה {work_order.id}",
                message=message,
                notification_type=notification_type,
                priority="medium",
                channel="in_app",
                entity_type="work_order",
                entity_id=work_order.id,
                data={
                    "work_order_id": work_order.id,
                    "supplier_id": work_order.supplier_id,
                    "equipment_type": work_order.equipment_type
                }
            )
            
            self.create_notification(db, notification)

    def create_supplier_response_notification(
        self,
        db: Session,
        work_order: WorkOrder,
        response: str
    ):
        """Create notification for supplier response."""
        if work_order.project and work_order.project.manager_id:
            message = f"ספק {work_order.supplier.company_name if work_order.supplier else 'לא ידוע'} {response} את ההזמנה"
            
            notification = NotificationCreate(
                user_id=work_order.project.manager_id,
                title=f"תגובת ספק - הזמנה {work_order.id}",
                message=message,
                notification_type="supplier_response",
                priority="high",
                channel="in_app",
                entity_type="work_order",
                entity_id=work_order.id,
                data={
                    "work_order_id": work_order.id,
                    "supplier_response": response,
                    "response_time": datetime.utcnow().isoformat()
                }
            )
            
            self.create_notification(db, notification)

    def create_budget_alert_notification(
        self,
        db: Session,
        project: Project,
        budget_usage_percentage: float
    ):
        """Create budget alert notification."""
        if project.manager_id:
            if budget_usage_percentage >= 90:
                priority = "critical"
                message = f"אזהרה קריטית: התקציב של פרויקט {project.name} נוצל ב-{budget_usage_percentage:.1f}%"
            elif budget_usage_percentage >= 75:
                priority = "high"
                message = f"אזהרה: התקציב של פרויקט {project.name} נוצל ב-{budget_usage_percentage:.1f}%"
            else:
                return  # No notification needed
            
            notification = NotificationCreate(
                user_id=project.manager_id,
                title="אזהרת תקציב",
                message=message,
                notification_type="budget_alert",
                priority=priority,
                channel="in_app",
                entity_type="project",
                entity_id=project.id,
                data={
                    "budget_usage_percentage": budget_usage_percentage,
                    "project_name": project.name
                }
            )
            
            self.create_notification(db, notification)

    def create_equipment_maintenance_notification(
        self,
        db: Session,
        equipment_id: int,
        maintenance_type: str,
        message: str
    ):
        """Create equipment maintenance notification."""
        # Get equipment manager or project manager
        # This would need to be implemented based on your equipment assignment logic
        
        notification = NotificationCreate(
            user_id=1,  # Placeholder - get actual manager ID
            title=f"תחזוקת ציוד - {maintenance_type}",
            message=message,
            notification_type="equipment_maintenance",
            priority="medium",
            data={
                "equipment_id": equipment_id,
                "maintenance_type": maintenance_type
            }
        )
        
        self.create_notification(db, notification)

    def create_system_notification(
        self,
        db: Session,
        title: str,
        message: str,
        priority: str = "medium",
        target_users: Optional[List[int]] = None
    ):
        """Create system-wide notification."""
        if target_users:
            for user_id in target_users:
                notification = NotificationCreate(
                    user_id=user_id,
                    title=title,
                    message=message,
                    notification_type="system",
                    priority=priority,
                    data={"system_notification": True}
                )
                
                self.create_notification(db, notification)
        else:
            # Send to all active users
            users = db.query(User).filter(User.is_active == True).all()
            for user in users:
                notification = NotificationCreate(
                    user_id=user.id,
                    title=title,
                    message=message,
                    notification_type="system",
                    priority=priority,
                    data={"system_notification": True}
                )
                
                self.create_notification(db, notification)

    def cleanup_old_notifications(self, db: Session, days_old: int = 30):
        """Clean up old notifications."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        deleted_count = (
            db.query(Notification)
            .filter(
                and_(
                    Notification.created_at < cutoff_date,
                    Notification.is_read == True,
                )
            )
            .update({"is_read": True})
        )
        
        db.commit()
        return deleted_count

    def get_notification_stats(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get notification statistics for user."""
        total_notifications = (
            db.query(Notification)
            .filter(
                and_(
                    Notification.user_id == user_id,
                )
            )
            .count()
        )
        
        unread_notifications = (
            db.query(Notification)
            .filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                )
            )
            .count()
        )
        
        critical_notifications = (
            db.query(Notification)
            .filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.priority == "critical",
                    Notification.is_read == False,
                )
            )
            .count()
        )
        
        return {
            "total": total_notifications,
            "unread": unread_notifications,
            "critical": critical_notifications,
            "read_percentage": (
                (total_notifications - unread_notifications) / total_notifications * 100
                if total_notifications > 0 else 0
            )
        }

    def _send_realtime_notification(self, notification: Notification):
        """Send real-time notification via WebSocket."""
        try:
            # This would integrate with your WebSocket service
            # For now, just log the notification
            print(f"Real-time notification sent: {notification.title} to user {notification.user_id}")
            
            # TODO: Implement WebSocket integration
            # websocket_manager.send_to_user(notification.user_id, {
            #     "type": "notification",
            #     "data": {
            #         "id": notification.id,
            #         "title": notification.title,
            #         "message": notification.message,
            #         "priority": notification.priority,
            #         "created_at": notification.created_at.isoformat()
            #     }
            # })
            
        except Exception as e:
            print(f"Error sending real-time notification: {e}")