# app/services/activity_log_service.py
"""Activity and audit logging service - Updated to match model."""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_, text
from sqlalchemy.orm import Session, joinedload

from app.models.activity_log import ActivityLog, ActivityType
from app.models.audit_log import AuditLog
from app.models.user import User


class ActivityLogService:
    """Service for activity and audit log operations."""

    def log_activity(
            self,
            db: Session,
            user_id: Optional[int],
            activity_type: ActivityType = None,
            action: str = None,
            entity_type: Optional[str] = None,
            entity_id: Optional[int] = None,
            details: Optional[Dict[str, Any]] = None,
            metadata: Optional[Dict[str, Any]] = None,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None,
            session_id: Optional[str] = None,
    ) -> ActivityLog:
        """Log user activity with full context."""
        import json
        
        # Use details parameter if provided, otherwise fallback to metadata
        details_data = details if details is not None else metadata
        
        # Convert dict to JSON string for SQL Server
        details_json = json.dumps(details_data, ensure_ascii=False) if details_data else None
        custom_metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        
        # Extract human-readable description from details
        description_text = None
        if details_data and isinstance(details_data, dict):
            description_text = details_data.get('description_he') or details_data.get('description')

        category = None
        act_str = str(activity_type or action or '').lower()
        if any(k in act_str for k in ('work_order', 'worklog', 'equipment', 'supplier', 'project')):
            category = 'operational'
        elif any(k in act_str for k in ('invoice', 'budget', 'payment', 'financial')):
            category = 'financial'
        elif any(k in act_str for k in ('user', 'role', 'permission', 'setting')):
            category = 'management'
        else:
            category = 'system'

        log = ActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details_json,
            description=description_text,
            custom_metadata=custom_metadata_json,
            category=category,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
        )

        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def log_audit(
            self,
            db: Session,
            table_name: str,
            record_id: int,
            action: str,  # "create", "update", "delete"
            old_values: Optional[Dict[str, Any]] = None,
            new_values: Optional[Dict[str, Any]] = None,
            user_id: Optional[int] = None,
            metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log database audit trail."""
        # Calculate changes
        changes = {}
        if action == "update" and old_values and new_values:
            for key in new_values:
                if key in old_values and old_values[key] != new_values[key]:
                    changes[key] = {"old": old_values[key], "new": new_values[key]}

        audit = AuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            changes=changes if changes else None,
            user_id=user_id,
            metadata=metadata or {},
        )

        db.add(audit)
        db.commit()
        db.refresh(audit)
        return audit

    def get_user_activities(
            self,
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 100,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            activity_type: Optional[ActivityType] = None,  # Changed
    ) -> List[ActivityLog]:
        """Get user activity logs."""
        query = db.query(ActivityLog).filter(ActivityLog.user_id == user_id)

        if start_date:
            query = query.filter(ActivityLog.created_at >= start_date)
        if end_date:
            query = query.filter(ActivityLog.created_at <= end_date)
        if activity_type:
            query = query.filter(ActivityLog.activity_type == activity_type)

        return (
            query.order_by(ActivityLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_activity_logs(
            self,
            db: Session,
            skip: int = 0,
            limit: int = 100,
            user_id: Optional[int] = None,
            activity_type: Optional[ActivityType] = None,
            action: Optional[str] = None,
            entity_type: Optional[str] = None,
            entity_id: Optional[int] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            ip_address: Optional[str] = None,
            search: Optional[str] = None,
    ) -> List[ActivityLog]:
        """Get activity logs with filters."""
        query = db.query(ActivityLog).options(joinedload(ActivityLog.user))

        if user_id:
            query = query.filter(ActivityLog.user_id == user_id)
        if activity_type:
            query = query.filter(ActivityLog.activity_type == activity_type)
        if action:
            query = query.filter(ActivityLog.action == action)
        if entity_type:
            query = query.filter(ActivityLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(ActivityLog.entity_id == entity_id)
        if start_date:
            query = query.filter(ActivityLog.created_at >= start_date)
        if end_date:
            query = query.filter(ActivityLog.created_at <= end_date)
        if ip_address:
            query = query.filter(ActivityLog.ip_address == ip_address)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    ActivityLog.action.ilike(search_term),
                    ActivityLog.description.ilike(search_term),
                    ActivityLog.entity_name.ilike(search_term),
                )
            )

        return (
            query.order_by(ActivityLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_activity_logs(
            self,
            db: Session,
            user_id: Optional[int] = None,
            activity_type: Optional[ActivityType] = None,
            action: Optional[str] = None,
            entity_type: Optional[str] = None,
            entity_id: Optional[int] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            ip_address: Optional[str] = None,
            search: Optional[str] = None,
    ) -> int:
        """Count activity logs with filters."""
        query = db.query(func.count(ActivityLog.id))

        if user_id:
            query = query.filter(ActivityLog.user_id == user_id)
        if activity_type:
            query = query.filter(ActivityLog.activity_type == activity_type)
        if action:
            query = query.filter(ActivityLog.action == action)
        if entity_type:
            query = query.filter(ActivityLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(ActivityLog.entity_id == entity_id)
        if start_date:
            query = query.filter(ActivityLog.created_at >= start_date)
        if end_date:
            query = query.filter(ActivityLog.created_at <= end_date)
        if ip_address:
            query = query.filter(ActivityLog.ip_address == ip_address)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    ActivityLog.action.ilike(search_term),
                    ActivityLog.description.ilike(search_term),
                    ActivityLog.entity_name.ilike(search_term),
                )
            )

        return query.scalar()

    def get_entity_history(
            self,
            db: Session,
            entity_type: str,
            entity_id: int,
            include_audit: bool = True,
            limit: int = 100
    ) -> Dict[str, Any]:
        """Get complete history for an entity."""
        # Activity logs
        activities = (
            db.query(ActivityLog)
            .filter(
                and_(
                    ActivityLog.entity_type == entity_type,
                    ActivityLog.entity_id == entity_id,
                )
            )
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
            .all()
        )

        history = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "activities": [
                {
                    "id": a.id,
                    "activity_type": a.activity_type.value,
                    "action": a.action,
                    "description": a.description,
                    "user_id": a.user_id,
                    "metadata": a.metadata,
                    "changes": a.changes,
                    "timestamp": a.created_at.isoformat(),
                }
                for a in activities
            ],
        }

        # Audit logs if requested
        if include_audit:
            # Map entity type to table name
            table_map = {
                "project": "projects",
                "user": "users",
                "equipment": "equipment",
                "work_order": "work_orders",
                "worklog": "worklogs",
                "invoice": "invoices",
            }

            table_name = table_map.get(entity_type)
            if table_name:
                audits = (
                    db.query(AuditLog)
                    .filter(
                        and_(
                            AuditLog.table_name == table_name,
                            AuditLog.record_id == entity_id,
                        )
                    )
                    .order_by(AuditLog.created_at.desc())
                    .limit(limit)
                    .all()
                )

                history["audits"] = [
                    {
                        "id": a.id,
                        "action": a.action,
                        "changes": a.changes,
                        "user_id": a.user_id,
                        "timestamp": a.created_at.isoformat(),
                    }
                    for a in audits
                ]

        return history

    def get_activity_summary(
            self,
            db: Session,
            start_date: date,
            end_date: date,
            user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get activity summary statistics."""
        query = db.query(ActivityLog).filter(
            and_(
                ActivityLog.created_at >= start_date,
                ActivityLog.created_at <= end_date
            )
        )

        if user_id:
            query = query.filter(ActivityLog.user_id == user_id)

        activities = query.all()

        # Unique users
        unique_users = len(set(a.user_id for a in activities if a.user_id))

        # Group by type
        type_counts = {}
        for activity in activities:
            activity_type = activity.activity_type.value
            if activity_type not in type_counts:
                type_counts[activity_type] = 0
            type_counts[activity_type] += 1

        # Group by action
        action_counts = {}
        for activity in activities:
            action = activity.action
            if action not in action_counts:
                action_counts[action] = 0
            action_counts[action] += 1

        # Group by day
        daily_counts = {}
        for activity in activities:
            day = activity.created_at.date().isoformat()
            if day not in daily_counts:
                daily_counts[day] = 0
            daily_counts[day] += 1

        # Group by hour
        hourly_counts = {}
        for activity in activities:
            hour = activity.created_at.hour
            if hour not in hourly_counts:
                hourly_counts[hour] = 0
            hourly_counts[hour] += 1

        # Most active users
        if not user_id:
            user_activity = (
                db.query(
                    ActivityLog.user_id,
                    User.full_name,
                    func.count(ActivityLog.id).label("count"),
                )
                .join(User, User.id == ActivityLog.user_id)
                .filter(
                    and_(
                        ActivityLog.created_at >= start_date,
                        ActivityLog.created_at <= end_date,
                    )
                )
                .group_by(ActivityLog.user_id, User.full_name)
                .order_by(text("count DESC"))
                .limit(10)
                .all()
            )

            most_active_users = [
                {"user_id": u[0], "name": u[1], "activity_count": u[2]}
                for u in user_activity
            ]
        else:
            most_active_users = []

        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_activities": len(activities),
            "unique_users": unique_users,
            "by_type": type_counts,
            "by_action": action_counts,
            "by_day": daily_counts,
            "by_hour": hourly_counts,
            "most_active_users": most_active_users,
        }

    def get_login_history(
            self,
            db: Session,
            user_id: Optional[int] = None,
            days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get login history."""
        cutoff = datetime.utcnow() - timedelta(days=days_back)

        query = db.query(ActivityLog).filter(
            and_(
                ActivityLog.activity_type.in_([
                    ActivityType.LOGIN,
                    ActivityType.LOGOUT,
                    ActivityType.LOGIN_FAILED
                ]),
                ActivityLog.created_at >= cutoff,
            )
        )

        if user_id:
            query = query.filter(ActivityLog.user_id == user_id)

        logins = query.order_by(ActivityLog.created_at.desc()).all()

        return [
            {
                "user_id": login.user_id,
                "activity_type": login.activity_type.value,
                "action": login.action,
                "ip_address": login.ip_address,
                "user_agent": login.user_agent,
                "timestamp": login.created_at.isoformat(),
            }
            for login in logins
        ]

    def detect_suspicious_activity(
            self,
            db: Session,
            hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """Detect suspicious activity patterns."""
        cutoff = datetime.utcnow() - timedelta(hours=hours_back)
        suspicious = []

        # Multiple failed logins
        failed_logins = (
            db.query(
                ActivityLog.user_id,
                ActivityLog.ip_address,
                func.count(ActivityLog.id).label("count"),
            )
            .filter(
                and_(
                    ActivityLog.activity_type == ActivityType.LOGIN_FAILED,
                    ActivityLog.created_at >= cutoff,
                )
            )
            .group_by(ActivityLog.user_id, ActivityLog.ip_address)
            .having(func.count(ActivityLog.id) >= 5)
            .all()
        )

        for f in failed_logins:
            suspicious.append(
                {
                    "type": "multiple_failed_logins",
                    "user_id": f[0],
                    "ip_address": f[1],
                    "count": f[2],
                    "severity": "high",
                }
            )

        # Unusual activity hours (outside 6am-10pm Israel time)
        night_activity = (
            db.query(
                ActivityLog.user_id,
                func.count(ActivityLog.id).label("count")
            )
            .filter(
                and_(
                    ActivityLog.created_at >= cutoff,
                    or_(
                        func.extract("hour", ActivityLog.created_at) < 6,
                        func.extract("hour", ActivityLog.created_at) > 22,
                    ),
                )
            )
            .group_by(ActivityLog.user_id)
            .having(func.count(ActivityLog.id) >= 10)
            .all()
        )

        for n in night_activity:
            suspicious.append(
                {
                    "type": "unusual_hours_activity",
                    "user_id": n[0],
                    "count": n[1],
                    "severity": "medium",
                }
            )

        # Mass data export/download
        data_access = (
            db.query(
                ActivityLog.user_id,
                ActivityLog.activity_type,
                func.count(ActivityLog.id).label("count"),
            )
            .filter(
                and_(
                    ActivityLog.created_at >= cutoff,
                    ActivityLog.activity_type.in_([
                        ActivityType.EXPORT,
                        ActivityType.DOWNLOAD
                    ]),
                )
            )
            .group_by(ActivityLog.user_id, ActivityLog.activity_type)
            .having(func.count(ActivityLog.id) >= 50)
            .all()
        )

        for d in data_access:
            suspicious.append(
                {
                    "type": "mass_data_access",
                    "user_id": d[0],
                    "activity_type": d[1].value,
                    "count": d[2],
                    "severity": "medium",
                }
            )

        return suspicious

    def cleanup_old_logs(
            self,
            db: Session,
            days_to_keep: int = 90
    ) -> Dict[str, int]:
        """Clean up old logs."""
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)

        # Delete old activity logs
        activity_count = (
            db.query(ActivityLog)
            .filter(ActivityLog.created_at < cutoff)
            .delete()
        )

        # Keep audit logs longer (1 year)
        audit_cutoff = datetime.utcnow() - timedelta(days=365)
        audit_count = (
            db.query(AuditLog)
            .filter(AuditLog.created_at < audit_cutoff)
            .delete()
        )

        db.commit()

        return {
            "activity_logs_deleted": activity_count,
            "audit_logs_deleted": audit_count,
        }
