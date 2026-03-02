"""
Worklog Service - optimized with eager loading
"""

from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, and_, or_

from app.models.worklog import Worklog
from app.models.work_order import WorkOrder
from app.models.user import User
from app.models.project import Project
from app.models.equipment import Equipment
from app.models.activity_type import ActivityType
from app.schemas.worklog import WorklogCreate, WorklogUpdate, WorklogSearch, WorklogStatistics
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException
from app.services import activity_logger


class WorklogService:
    """
    Worklog Service - TRANSACTIONS category
    
    Note: NOT inheriting BaseService because worklogs doesn't have deleted_at
    Uses is_active for deactivation instead.
    """
    
    def _generate_report_number(self, db: Session) -> int:
        """Generate unique report number"""
        max_num = db.query(func.max(Worklog.report_number)).scalar() or 0
        return max_num + 1
    
    def create(self, db: Session, data: WorklogCreate, current_user_id: int) -> Worklog:
        """Create worklog with FK validation"""
        # Validate FK: work_order (REQUIRED)
        wo = db.query(WorkOrder).filter_by(id=data.work_order_id).first()
        if not wo:
            raise ValidationException(f"Work order {data.work_order_id} not found")
        
        # Derive missing fields from work_order
        user_id = data.user_id or current_user_id
        project_id = data.project_id or wo.project_id
        
        # Validate FK: user
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValidationException(f"User {user_id} not found")
        
        # Validate FK: project
        project = db.query(Project).filter_by(id=project_id).first()
        if not project:
            raise ValidationException(f"Project {project_id} not found")
        
        # Validate FK: equipment (if provided)
        if data.equipment_id:
            eq = db.query(Equipment).filter_by(id=data.equipment_id).first()
            if not eq:
                raise ValidationException(f"Equipment {data.equipment_id} not found")
        
        # Validate FK: activity_type (optional for storage type)
        activity_type_id = data.activity_type_id
        if activity_type_id:
            act = db.query(ActivityType).filter_by(id=activity_type_id).first()
            if not act:
                raise ValidationException(f"Activity type {activity_type_id} not found")
        
        # Generate report_number
        report_number = self._generate_report_number(db)
        
        # Create
        worklog_dict = data.model_dump(exclude_unset=True)
        worklog_dict['report_number'] = report_number
        worklog_dict['report_type'] = data.report_type or 'standard'  # use provided or default
        
        # Override with derived values
        worklog_dict['user_id'] = user_id
        worklog_dict['project_id'] = project_id
        if activity_type_id:
            worklog_dict['activity_type_id'] = activity_type_id
        
        worklog = Worklog(**worklog_dict)
        db.add(worklog)
        db.commit()
        db.refresh(worklog)
        
        # Log activity
        activity_logger.log_worklog_created(
            db=db,
            worklog_id=worklog.id,
            user_id=current_user_id,
            work_order_id=data.work_order_id,
            project_id=project_id,
            is_standard=worklog.report_type == 'standard'
        )
        
        return worklog
    
    def get_by_id(self, db: Session, worklog_id: int) -> Optional[Worklog]:
        """Get worklog by ID"""
        return db.query(Worklog).filter_by(id=worklog_id).first()
    
    def update(self, db: Session, worklog_id: int, data: WorklogUpdate, current_user_id: int) -> Worklog:
        """Update worklog"""
        worklog = self.get_by_id(db, worklog_id)
        if not worklog:
            raise NotFoundException(f"Worklog {worklog_id} not found")
        
        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(worklog, field, value)
        
        db.commit()
        db.refresh(worklog)
        return worklog
    
    def list(self, db: Session, search: WorklogSearch) -> Tuple[List[Worklog], int]:
        """List worklogs with filters - optimized with eager loading"""
        # Use eager loading to prevent N+1 queries
        query = db.query(Worklog).options(
            joinedload(Worklog.user),
            joinedload(Worklog.project),
            joinedload(Worklog.work_order),
            joinedload(Worklog.equipment),
            joinedload(Worklog.activity_type)
        )
        
        # Build base count query (without eager loading)
        count_query = db.query(func.count(Worklog.id))
        
        # Active only (TRANSACTIONS uses is_active, not deleted_at)
        if search.is_active is not None:
            query = query.filter(Worklog.is_active == search.is_active)
            count_query = count_query.filter(Worklog.is_active == search.is_active)
        elif search.is_active is None:
            # Default: show only active
            query = query.filter(Worklog.is_active == True)
            count_query = count_query.filter(Worklog.is_active == True)
        
        # Filters
        if search.work_order_id:
            query = query.filter(Worklog.work_order_id == search.work_order_id)
            count_query = count_query.filter(Worklog.work_order_id == search.work_order_id)
        if search.user_id:
            query = query.filter(Worklog.user_id == search.user_id)
            count_query = count_query.filter(Worklog.user_id == search.user_id)
        if search.project_id:
            query = query.filter(Worklog.project_id == search.project_id)
            count_query = count_query.filter(Worklog.project_id == search.project_id)
        if search.area_id is not None:
            area_project_ids = select(Project.id).where(Project.area_id == search.area_id)
            query = query.filter(Worklog.project_id.in_(area_project_ids))
            count_query = count_query.filter(Worklog.project_id.in_(area_project_ids))
        if search.equipment_id:
            query = query.filter(Worklog.equipment_id == search.equipment_id)
            count_query = count_query.filter(Worklog.equipment_id == search.equipment_id)
        if search.status:
            query = query.filter(Worklog.status == search.status)
            count_query = count_query.filter(Worklog.status == search.status)
        if search.date_from:
            query = query.filter(Worklog.report_date >= search.date_from)
            count_query = count_query.filter(Worklog.report_date >= search.date_from)
        if search.date_to:
            query = query.filter(Worklog.report_date <= search.date_to)
            count_query = count_query.filter(Worklog.report_date <= search.date_to)
        
        # Count (single query)
        total = count_query.scalar() or 0
        
        # Sort
        sort_col = getattr(Worklog, search.sort_by, Worklog.report_date)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        # Paginate
        offset = (search.page - 1) * search.page_size
        worklogs = query.offset(offset).limit(search.page_size).all()
        
        return worklogs, total
    
    def submit(self, db: Session, worklog_id: int, current_user_id: int) -> Worklog:
        """Submit worklog for approval"""
        worklog = self.get_by_id(db, worklog_id)
        if not worklog:
            raise NotFoundException(f"Worklog {worklog_id} not found")
        
        worklog.status = 'SUBMITTED'
        db.commit()
        db.refresh(worklog)
        
        # Log activity
        activity_logger.log_worklog_submitted(
            db=db,
            worklog_id=worklog.id,
            user_id=current_user_id,
            project_id=worklog.project_id,
            work_order_id=worklog.work_order_id
        )

        # Notify area/region managers
        _notify_managers_worklog_submitted(db, worklog)

        return worklog
    
    def approve(self, db: Session, worklog_id: int, current_user_id: int) -> Worklog:
        """Approve worklog"""
        worklog = self.get_by_id(db, worklog_id)
        if not worklog:
            raise NotFoundException(f"Worklog {worklog_id} not found")
        
        worklog.status = 'APPROVED'
        db.commit()
        db.refresh(worklog)
        
        # Log activity
        activity_logger.log_worklog_approved(
            db=db,
            worklog_id=worklog.id,
            user_id=current_user_id,
            approved_by_id=current_user_id,
            project_id=worklog.project_id,
            work_order_id=worklog.work_order_id
        )

        # Audit log
        _audit_worklog(db, current_user_id, worklog.id, 'APPROVE')

        return worklog
    
    def reject(self, db: Session, worklog_id: int, current_user_id: int, reason: str = None) -> Worklog:
        """Reject worklog"""
        worklog = self.get_by_id(db, worklog_id)
        if not worklog:
            raise NotFoundException(f"Worklog {worklog_id} not found")
        
        worklog.status = 'REJECTED'
        db.commit()
        db.refresh(worklog)
        
        # Log activity
        activity_logger.log_worklog_rejected(
            db=db,
            worklog_id=worklog.id,
            user_id=current_user_id,
            rejected_by_id=current_user_id,
            reason=reason,
            project_id=worklog.project_id,
            work_order_id=worklog.work_order_id
        )
        
        return worklog
    
    def deactivate(self, db: Session, worklog_id: int, current_user_id: int) -> Worklog:
        """Deactivate worklog (TRANSACTIONS uses is_active, not deleted_at)"""
        worklog = self.get_by_id(db, worklog_id)
        if not worklog:
            raise NotFoundException(f"Worklog {worklog_id} not found")
        
        worklog.is_active = False
        db.commit()
        db.refresh(worklog)
        return worklog
    
    def activate(self, db: Session, worklog_id: int, current_user_id: int) -> Worklog:
        """Activate worklog"""
        worklog = db.query(Worklog).filter_by(id=worklog_id).first()
        if not worklog:
            raise NotFoundException(f"Worklog {worklog_id} not found")
        
        worklog.is_active = True
        db.commit()
        db.refresh(worklog)
        return worklog
    
    def get_statistics(self, db: Session, filters: Optional[dict] = None) -> WorklogStatistics:
        """Get statistics"""
        query = db.query(Worklog).filter(Worklog.is_active == True)
        
        if filters:
            if filters.get('project_id'):
                query = query.filter(Worklog.project_id == filters['project_id'])
            if filters.get('date_from'):
                query = query.filter(Worklog.report_date >= filters['date_from'])
            if filters.get('date_to'):
                query = query.filter(Worklog.report_date <= filters['date_to'])
        
        worklogs = query.all()
        
        stats = WorklogStatistics(
            total=len(worklogs),
            total_hours=sum(wl.work_hours or 0 for wl in worklogs),
            total_cost=sum(wl.cost_with_vat or 0 for wl in worklogs)
        )
        
        # By status
        by_status = {}
        for wl in worklogs:
            if wl.status:
                by_status[wl.status] = by_status.get(wl.status, 0) + 1
        stats.by_status = by_status
        
        return stats


# ── Notification helpers ──────────────────────────────────────────────────────

def _notify_managers_worklog_submitted(db, worklog):
    """Notify area/region managers when a worklog is submitted for approval."""
    import logging, json
    log = logging.getLogger(__name__)
    try:
        from sqlalchemy import text
        from app.services.notification_service import notification_service
        from app.schemas.notification import NotificationCreate

        if not worklog.project_id:
            return

        # Get project info
        proj = db.execute(text("""
            SELECT p.name, p.area_id, a.region_id
            FROM projects p LEFT JOIN areas a ON p.area_id = a.id
            WHERE p.id = :pid
        """), {"pid": worklog.project_id}).first()
        if not proj:
            return

        project_name = proj[0] or f"פרויקט {worklog.project_id}"
        area_id = proj[1]
        region_id = proj[2]

        # Find managers
        managers = db.execute(text("""
            SELECT DISTINCT u.id FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.code IN ('AREA_MANAGER','REGION_MANAGER','ADMIN','ORDER_COORDINATOR')
              AND u.is_active = true
              AND (u.area_id = :aid OR u.region_id = :rid OR r.code = 'ADMIN')
        """), {"aid": area_id, "rid": region_id}).fetchall()

        for row in managers:
            notif = NotificationCreate(
                user_id=row[0],
                title=f"דיווח שעות ממתין לאישור — {project_name}",
                message=f"דיווח שעות חדש בפרויקט {project_name} ממתין לאישורך.",
                notification_type="WORKLOG_PENDING",
                priority="medium",
                channel="in_app",
                entity_type="worklog",
                entity_id=worklog.id,
                data=json.dumps({"worklog_id": worklog.id, "project_id": worklog.project_id}),
                action_url=f"/worklogs/{worklog.id}",
            )
            notification_service.create_notification(db, notif)
    except Exception as e:
        log.warning(f"Worklog submit notification failed: {e}")


def _audit_worklog(db, user_id: int, worklog_id: int, action: str):
    """Insert audit log for worklog status change."""
    import logging, json
    try:
        from sqlalchemy import text
        db.execute(text("""
            INSERT INTO audit_logs (user_id, table_name, record_id, action, new_values)
            VALUES (:uid, 'worklogs', :rid, :act, :nv::jsonb)
        """), {"uid": user_id, "rid": worklog_id, "act": action,
               "nv": json.dumps({"action": action, "worklog_id": worklog_id})})
        db.commit()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Worklog audit log failed: {e}")
