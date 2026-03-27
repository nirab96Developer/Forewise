"""
Worklog Service - optimized with eager loading
"""

from datetime import datetime
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
        """Generate unique report number (sequential integer, displayed as WL-YYYY-XXXX)"""
        max_num = db.query(func.max(Worklog.report_number)).scalar() or 0
        return max_num + 1

    @staticmethod
    def format_report_number(report_number: int) -> str:
        """Format report number for display: WL-2026-0047"""
        from datetime import datetime
        return f"WL-{datetime.now().year}-{str(report_number).zfill(4)}"

    def _resolve_hourly_rate(self, db: Session, worklog_dict: dict) -> float:
        """Resolve hourly rate from work order or equipment type."""
        wo_id = worklog_dict.get('work_order_id')
        if wo_id:
            wo = db.query(WorkOrder).filter_by(id=wo_id).first()
            if wo and wo.hourly_rate:
                return float(wo.hourly_rate)
            if wo and wo.equipment_type:
                from app.models.equipment_type import EquipmentType
                et = db.query(EquipmentType).filter(
                    EquipmentType.name.ilike(wo.equipment_type),
                    EquipmentType.is_active == True
                ).first()
                if et:
                    return float(et.default_hourly_rate)
        eq_type_id = worklog_dict.get('equipment_type_id')
        if eq_type_id:
            from app.models.equipment_type import EquipmentType
            et = db.query(EquipmentType).filter_by(id=eq_type_id).first()
            if et:
                return float(et.default_hourly_rate)
        return 0
    
    def create(self, db: Session, data: WorklogCreate, current_user_id: int) -> Worklog:
        """Create worklog with FK validation"""
        # Validate FK: work_order (optional — can create standalone worklog)
        wo = None
        if data.work_order_id:
            wo = db.query(WorkOrder).filter_by(id=data.work_order_id).first()
            if not wo:
                raise ValidationException(f"Work order {data.work_order_id} not found")
        
        # Auto-inherit equipment from work order if not provided
        if wo and not data.equipment_id and wo.equipment_id:
            data.equipment_id = wo.equipment_id

        # Warn if no equipment scan exists for this WO
        if wo:
            from sqlalchemy import text as sa_text
            scan_exists = db.execute(sa_text(
                "SELECT 1 FROM equipment_scans WHERE work_order_id = :woid LIMIT 1"
            ), {"woid": wo.id}).fetchone()
            if not scan_exists:
                import logging
                logging.getLogger(__name__).warning(
                    f"Worklog created for WO {wo.id} without prior equipment scan"
                )

        # Derive missing fields from work_order
        user_id = data.user_id or current_user_id
        project_id = data.project_id or (wo.project_id if wo else None)
        supplier_id = (data.supplier_id if hasattr(data, 'supplier_id') and data.supplier_id else None) or (wo.supplier_id if wo else None)
        
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
        worklog_dict['report_type'] = data.report_type or 'standard'
        
        # Override with derived values
        worklog_dict['user_id'] = user_id
        worklog_dict['project_id'] = project_id
        if supplier_id:
            worklog_dict['supplier_id'] = supplier_id
        if activity_type_id:
            worklog_dict['activity_type_id'] = activity_type_id
        
        # Map frontend field names to model field names
        if 'work_date' in worklog_dict and not worklog_dict.get('report_date'):
            worklog_dict['report_date'] = worklog_dict.pop('work_date')
        else:
            worklog_dict.pop('work_date', None)
        
        if 'description' in worklog_dict and not worklog_dict.get('activity_description'):
            worklog_dict['activity_description'] = worklog_dict.pop('description')
        else:
            worklog_dict.pop('description', None)
            
        if not worklog_dict.get('work_hours') and worklog_dict.get('total_hours'):
            worklog_dict['work_hours'] = worklog_dict['total_hours']
        
        # Always compute total_hours, net_hours, paid_hours
        wh = float(worklog_dict.get('work_hours') or 0)
        bh = float(worklog_dict.get('break_hours') or 0)
        if wh > 0 and not worklog_dict.get('total_hours'):
            worklog_dict['total_hours'] = round(wh + bh, 2)
        if wh > 0 and not worklog_dict.get('net_hours'):
            worklog_dict['net_hours'] = round(wh, 2)
        if wh > 0 and not worklog_dict.get('paid_hours'):
            worklog_dict['paid_hours'] = round(wh, 2)
        
        # Persist equipment_scanned if sent
        if 'equipment_scanned' in worklog_dict:
            pass  # model has this column, keep it

        includes_guard = bool(worklog_dict.pop('includes_guard', False))
        # Client may send these; we normalize from includes_guard below
        worklog_dict.pop('is_overnight', None)
        worklog_dict.pop('overnight_nights', None)
        worklog_dict.pop('overnight_rate', None)
        
        # Save segments before removing from worklog_dict
        segments_data = worklog_dict.pop('segments', None) or []

        # Remove fields that don't exist on the Worklog model
        for key in ['activity_type', 'activity',
                     'billable_hours', 'non_standard_notes']:
            worklog_dict.pop(key, None)
        
        # Set initial status
        if not worklog_dict.get('status'):
            worklog_dict['status'] = 'PENDING'

        # לינת שטח — from unified form checkbox (includes_guard)
        overnight_total = 0.0
        if includes_guard:
            worklog_dict['is_overnight'] = True
            worklog_dict['overnight_nights'] = 1
            worklog_dict['overnight_rate'] = Decimal('250')
            overnight_total = 250.0
        
        # Calculate hourly_rate_snapshot and costs
        rate = None
        if not worklog_dict.get('hourly_rate_snapshot'):
            rate = self._resolve_hourly_rate(db, worklog_dict)
            if rate:
                worklog_dict['hourly_rate_snapshot'] = rate
        else:
            rate = float(worklog_dict['hourly_rate_snapshot'])

        hours = float(worklog_dict.get('work_hours') or worklog_dict.get('total_hours') or 0)
        if rate:
            rate_f = float(rate)
            worklog_dict['cost_before_vat'] = round(hours * rate_f + overnight_total, 2)
            worklog_dict['vat_rate'] = 17.0
            worklog_dict['cost_with_vat'] = round(worklog_dict['cost_before_vat'] * 1.17, 2)
        elif overnight_total:
            worklog_dict['cost_before_vat'] = round(overnight_total, 2)
            worklog_dict['vat_rate'] = 17.0
            worklog_dict['cost_with_vat'] = round(worklog_dict['cost_before_vat'] * 1.17, 2)

        if includes_guard:
            worklog_dict['overnight_total'] = Decimal(str(overnight_total))
        
        worklog = Worklog(**worklog_dict)
        db.add(worklog)
        db.commit()
        db.refresh(worklog)

        # Save non-standard time segments
        if segments_data:
            try:
                from app.models.worklog_segment import WorklogSegment
                for seg in segments_data:
                    if isinstance(seg, dict):
                        db.add(WorklogSegment(
                            worklog_id=worklog.id,
                            segment_type=seg.get('type', seg.get('segment_type', 'work')),
                            start_time=seg.get('start_time'),
                            end_time=seg.get('end_time'),
                            notes=seg.get('notes', ''),
                        ))
                db.commit()
            except Exception as seg_err:
                import logging
                logging.getLogger(__name__).warning(f"Segment save failed for WL {worklog.id}: {seg_err}")

        # Log activity
        wo_title = ""
        if wo:
            wo_title = getattr(wo, 'title', '') or getattr(wo, 'equipment_type', '') or ''
        activity_logger.log_worklog_created(
            db=db,
            worklog_id=worklog.id,
            user_id=current_user_id,
            work_order_id=data.work_order_id,
            project_id=project_id,
            is_standard=worklog.report_type == 'standard',
            total_hours=float(worklog.work_hours or worklog.total_hours or 0),
            work_order_title=wo_title
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
        if search.supplier_id:
            query = query.filter(Worklog.supplier_id == search.supplier_id)
            count_query = count_query.filter(Worklog.supplier_id == search.supplier_id)
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
        from sqlalchemy import text as sa_text
        worklog = self.get_by_id(db, worklog_id)
        if not worklog:
            raise NotFoundException(f"Worklog {worklog_id} not found")
        
        worklog.status = 'SUBMITTED'

        # Compute hours for metadata
        hours_meta = {}
        if worklog.work_order_id:
            try:
                row = db.execute(sa_text("""
                    SELECT COALESCE(SUM(work_hours),0) as used
                    FROM worklogs
                    WHERE work_order_id = :wid AND UPPER(status) != 'REJECTED'
                      AND is_active = true AND id != :lid
                """), {"wid": worklog.work_order_id, "lid": worklog_id}).first()
                wo_row = db.execute(sa_text(
                    "SELECT estimated_hours FROM work_orders WHERE id=:wid"
                ), {"wid": worklog.work_order_id}).first()
                used_before = float(row.used) if row else 0
                this_hours = float(worklog.work_hours or 0)
                used_total = used_before + this_hours
                estimated = float(wo_row.estimated_hours or 0) if wo_row else 0
                remaining = max(estimated - used_total, 0)
                hours_meta = {
                    "hours_reported": this_hours,
                    "hours_remaining": remaining,
                    "days_remaining": round(remaining / 9, 1),
                }
            except Exception:
                pass

        # Enrich metadata_json
        if hours_meta:
            import json
            try:
                existing = json.loads(worklog.metadata_json or '{}') if worklog.metadata_json else {}
                existing.update(hours_meta)
                worklog.metadata_json = json.dumps(existing)
            except Exception:
                pass

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

        # Notify if remaining hours < 9
        if hours_meta.get("hours_remaining", 9) < 9 and worklog.work_order_id:
            _notify_low_hours(db, worklog, hours_meta)

        return worklog
    
    def approve(self, db: Session, worklog_id: int, current_user_id: int) -> Worklog:
        """Approve worklog"""
        worklog = self.get_by_id(db, worklog_id)
        if not worklog:
            raise NotFoundException(f"Worklog {worklog_id} not found")
        
        from datetime import datetime as _dt
        worklog.status = 'APPROVED'
        worklog.approved_by_user_id = current_user_id
        worklog.approved_at = _dt.utcnow()
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

        # Release budget incrementally + check auto-completion
        try:
            if worklog.work_order_id:
                from app.models.budget import Budget

                wo = db.query(WorkOrder).filter(WorkOrder.id == worklog.work_order_id).first()
                if wo and wo.project_id:
                    cost = float(worklog.work_hours or 0) * float(worklog.hourly_rate_snapshot or 0)
                    cost += float(worklog.overnight_nights or 0) * 250

                    budget = (
                        db.query(Budget)
                        .filter(
                            Budget.project_id == wo.project_id,
                            Budget.is_active == True,
                            Budget.deleted_at.is_(None),
                        )
                        .first()
                    )
                    if budget and cost > 0:
                        release = min(cost, float(wo.remaining_frozen or 0))
                        budget.committed_amount = max(Decimal(0), (budget.committed_amount or Decimal(0)) - Decimal(str(release)))
                        budget.spent_amount = (budget.spent_amount or Decimal(0)) + Decimal(str(cost))
                        budget.remaining_amount = (budget.total_amount or Decimal(0)) - (budget.committed_amount or Decimal(0)) - (budget.spent_amount or Decimal(0))
                        wo.remaining_frozen = max(Decimal(0), (wo.remaining_frozen or Decimal(0)) - Decimal(str(release)))
                        db.flush()

                    # Auto-complete when all frozen budget is consumed
                    if wo and (wo.remaining_frozen or 0) <= 0 and float(wo.frozen_amount or 0) > 0:
                        wo.status = 'COMPLETED'
                        wo.updated_at = datetime.utcnow()
                        if wo.equipment_id:
                            eq = db.query(Equipment).filter(Equipment.id == wo.equipment_id).first()
                            if eq:
                                eq.assigned_project_id = None
                        db.commit()
                        import logging
                        logging.getLogger(__name__).info(
                            f"WO {wo.id} auto-completed: frozen budget fully consumed"
                        )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Budget release/completion check failed: {e}")

        # Send approval emails (stage 2)
        try:
            _send_worklog_approved_emails(db, worklog)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Worklog approval email failed: {e}")

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


#  Notification helpers 

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


def _notify_low_hours(db, worklog, hours_meta: dict):
    """Send high-priority notification when work order has < 9 remaining hours."""
    try:
        from app.services.notification_service import notification_service
        from app.schemas.notification import NotificationCreate
        from sqlalchemy import text

        remaining = hours_meta.get("hours_remaining", 0)
        wo_row = db.execute(text(
            "SELECT id, title, equipment_type, created_by_id FROM work_orders WHERE id=:wid"
        ), {"wid": worklog.work_order_id}).first()
        if not wo_row:
            return
        title_body = f" יתרת שעות נמוכה — {wo_row.equipment_type or 'כלי'}"
        body = f"נשארו {remaining:.1f} שעות בלבד מהזמנה #{worklog.work_order_id}. שקול להזמין המשך."

        # Notify work order creator
        recipients = set()
        if wo_row.created_by_id:
            recipients.add(wo_row.created_by_id)
        # Also notify area managers of the project
        if worklog.project_id:
            rows = db.execute(text("""
                SELECT DISTINCT u.id FROM users u
                JOIN roles r ON u.role_id = r.id
                JOIN project_assignments pa ON pa.user_id = u.id
                WHERE pa.project_id = :pid AND u.is_active = true
                  AND r.code IN ('AREA_MANAGER','REGION_MANAGER')
            """), {"pid": worklog.project_id}).fetchall()
            for r in rows:
                recipients.add(r[0])

        for uid in recipients:
            notif = NotificationCreate(
                user_id=uid,
                title=title_body,
                message=body,
                notification_type="EQUIPMENT_LOW_HOURS",
                priority="high",
                link=f"/work-orders/{worklog.work_order_id}",
            )
            notification_service.create_notification(db, notif)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Low hours notification failed: {e}")


def _audit_worklog(db, user_id: int, worklog_id: int, action: str):
    """Insert audit log for worklog status change."""
    import logging, json
    try:
        from sqlalchemy import text
        db.execute(text("""
            INSERT INTO audit_logs (user_id, table_name, record_id, action, new_values)
            VALUES (:uid, 'worklogs', :rid, :act, CAST(:nv AS jsonb))
        """), {"uid": user_id, "rid": worklog_id, "act": action,
               "nv": json.dumps({"action": action, "worklog_id": worklog_id})})
        db.commit()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Worklog audit log failed: {e}")
        try:
            db.rollback()
        except Exception:
            pass


#  Segments + Overnight calculation 

MAX_NET_HOURS_PER_DAY = 12.0

SEGMENT_TYPES = {"work", "rest", "idle", "travel", "overnight"}
ACTIVITY_TYPES = {"נטיעה", "ניקוי", "גיזום", "תחזוקה", "הסעה", "פיקוח", "אחר"}


def _calc_duration(start: str, end: str) -> float:
    """HH:MM  hours (float)"""
    from datetime import datetime as _dt
    fmt = "%H:%M"
    s = _dt.strptime(start, fmt)
    e = _dt.strptime(end, fmt)
    diff = (e - s).total_seconds()
    if diff < 0:
        diff += 86400  # overnight segment
    return round(diff / 3600, 2)


def calculate_worklog_totals(
    segments: list,
    is_overnight: bool,
    overnight_nights: int,
    overnight_rate: float,
    hourly_rate: float,
    vat_rate: float = 0.17,
) -> dict:
    """
    קלט: רשימת segments, דגל is_overnight
    פלט: net_hours, paid_hours, overnight_total, cost_before_vat, cost_with_vat

    כלל: מנוחה = 0% | עבודה = payment_pct% | אחר = payment_pct%
    ולידציה: מקסימום 12 שעות net ביום
    """
    net_hours = 0.0
    paid_hours = 0.0

    for seg in segments:
        seg_type = seg.get("segment_type", "work")
        start = seg.get("start_time", "00:00")
        end = seg.get("end_time", "00:00")
        dur = seg.get("duration_hours") or _calc_duration(start, end)
        pct = seg.get("payment_pct", 100)

        net_hours += dur
        if seg_type == "rest":
            pass  # 0%
        else:
            paid_hours += dur * (pct / 100)

    if net_hours > MAX_NET_HOURS_PER_DAY:
        raise ValueError(
            f"חריגה ממקסימום שעות ביום ({MAX_NET_HOURS_PER_DAY}). דווח: {net_hours:.1f}"
        )

    overnight_total = 0.0
    if is_overnight and overnight_rate and overnight_nights:
        overnight_total = float(overnight_rate) * int(overnight_nights)

    cost_before_vat = round(paid_hours * hourly_rate + overnight_total, 2)
    cost_with_vat = round(cost_before_vat * (1 + vat_rate), 2)

    return {
        "net_hours": round(net_hours, 2),
        "paid_hours": round(paid_hours, 2),
        "overnight_total": round(overnight_total, 2),
        "cost_before_vat": cost_before_vat,
        "cost_with_vat": cost_with_vat,
    }


def save_worklog_with_segments(
    worklog_id: int,
    segments: list,
    is_overnight: bool,
    overnight_nights: int,
    db,
) -> dict:
    """
    שומר segments לטבלה, מחשב totals, מעדכן worklog.
    """
    from app.models.worklog import Worklog
    from app.models.worklog_segment import WorklogSegment
    from app.services.rate_service import get_equipment_rate

    wl = db.query(Worklog).filter(Worklog.id == worklog_id).first()
    if not wl:
        raise ValueError("דיווח לא נמצא")

    # נקה segments קיימים
    db.query(WorklogSegment).filter(WorklogSegment.worklog_id == worklog_id).delete()

    # קבל תעריף
    rate_info = get_equipment_rate(wl.equipment_id, wl.supplier_id, db)
    hourly_rate = float(wl.hourly_rate_snapshot or rate_info["hourly_rate"] or 0)
    overnight_rate = rate_info["overnight_rate"]

    # חשב totals
    totals = calculate_worklog_totals(
        segments=segments,
        is_overnight=is_overnight,
        overnight_nights=overnight_nights,
        overnight_rate=overnight_rate,
        hourly_rate=hourly_rate,
        vat_rate=float(wl.vat_rate or 0.17),
    )

    # שמור segments
    for i, seg in enumerate(segments):
        duration = seg.get("duration_hours") or _calc_duration(
            seg.get("start_time", "00:00"), seg.get("end_time", "00:00")
        )
        ws = WorklogSegment(
            worklog_id=worklog_id,
            segment_type=seg.get("segment_type", "work"),
            activity_type=seg.get("activity_type"),
            start_time=seg.get("start_time", "00:00"),
            end_time=seg.get("end_time", "00:00"),
            duration_hours=duration,
            payment_pct=seg.get("payment_pct", 100),
            amount=round(duration * (seg.get("payment_pct", 100) / 100) * hourly_rate, 2),
            notes=seg.get("notes"),
        )
        db.add(ws)

    # עדכן worklog
    wl.net_hours = totals["net_hours"]
    wl.paid_hours = totals["paid_hours"]
    wl.is_overnight = is_overnight
    wl.overnight_nights = overnight_nights
    wl.overnight_rate = overnight_rate
    wl.overnight_total = totals["overnight_total"]
    wl.cost_before_vat = totals["cost_before_vat"]
    wl.cost_with_vat = totals["cost_with_vat"]
    wl.total_amount = totals["cost_with_vat"]
    wl.hourly_rate_snapshot = hourly_rate

    db.commit()
    db.refresh(wl)
    return totals


def _send_worklog_created_email(db, worklog, current_user_id: int):
    """Send Stage 1 email: accountant gets 'דיווח WL-XXXX ממתין לאישורך'."""
    import logging
    log = logging.getLogger(__name__)
    try:
        from app.core.email import send_email
        from sqlalchemy import text

        report_number = WorklogService.format_report_number(worklog.report_number or worklog.id)
        project_name = ""
        if worklog.project_id:
            row = db.execute(text("SELECT name FROM projects WHERE id=:pid"), {"pid": worklog.project_id}).first()
            if row:
                project_name = row[0] or ""

        acct_rows = db.execute(text("""
            SELECT u.email FROM users u JOIN roles r ON u.role_id=r.id
            WHERE r.code='ACCOUNTANT' AND u.is_active=true AND u.email IS NOT NULL
        """)).fetchall()

        for row in acct_rows:
            send_email(
                to=row[0],
                subject=f"דיווח {report_number} ממתין לאישורך",
                body=(
                    f"שלום,\n\n"
                    f"דיווח שעות {report_number} ממתין לאישורך.\n"
                    f"פרויקט: {project_name}\n"
                    f"שעות: {float(worklog.work_hours or 0)}\n\n"
                    "Forewise"
                ),
            )
    except Exception as e:
        log.warning(f"Worklog Stage 1 email failed: {e}")


def _send_worklog_approved_emails(db, worklog):
    """Send Stage 2 approval emails to supplier and work manager."""
    from app.core.email import send_email
    from app.templates.email_worklog import stage2_approved
    from sqlalchemy import text

    report_number = WorklogService.format_report_number(worklog.report_number or worklog.id)
    project_name = ""
    supplier_name = ""
    supplier_email = ""
    worker_email = ""
    worker_name = ""
    equipment_type = worklog.equipment_type or ""

    if worklog.project_id:
        row = db.execute(text("SELECT name FROM projects WHERE id=:pid"), {"pid": worklog.project_id}).first()
        if row:
            project_name = row[0]

    if worklog.work_order_id:
        row = db.execute(text(
            "SELECT s.name, s.email FROM work_orders wo JOIN suppliers s ON wo.supplier_id=s.id WHERE wo.id=:wid"
        ), {"wid": worklog.work_order_id}).first()
        if row:
            supplier_name, supplier_email = row[0], row[1]

    if worklog.user_id:
        row = db.execute(text("SELECT full_name, email FROM users WHERE id=:uid"), {"uid": worklog.user_id}).first()
        if row:
            worker_name, worker_email = row[0] or "", row[1] or ""

    work_date = str(worklog.report_date or "")
    total_hours = float(worklog.total_hours or worklog.work_hours or 0)
    hourly_rate = float(worklog.hourly_rate_snapshot or 0)
    overnight_nights = int(worklog.overnight_nights or 0)
    overnight_rate = float(worklog.overnight_rate or 250)

    for role, email in [("supplier", supplier_email), ("worker", worker_email)]:
        if not email:
            continue
        tmpl = stage2_approved(
            report_number=report_number,
            project_name=project_name,
            supplier_name=supplier_name,
            equipment_type=equipment_type,
            work_date=work_date,
            total_hours=total_hours,
            hourly_rate=hourly_rate,
            overnight_nights=overnight_nights,
            overnight_rate=overnight_rate,
            worker_name=worker_name,
            recipient_role=role,
        )
        send_email(to=email, subject=tmpl["subject"], body="", html_body=tmpl["html"])


def send_worklog_invoiced_emails(db, worklogs, invoice):
    """Stage 3: Send emails when worklogs are marked INVOICED.
    Recipients: supplier + work_manager of each worklog.
    """
    import logging
    log = logging.getLogger(__name__)
    try:
        from app.core.email import send_email
        from sqlalchemy import text

        if not worklogs:
            return

        invoice_number = getattr(invoice, 'invoice_number', None) or getattr(invoice, 'id', '')
        invoice_date = str(getattr(invoice, 'invoice_date', '') or getattr(invoice, 'created_at', '') or '')
        total_amount = float(getattr(invoice, 'total_amount', 0) or 0)

        project_name = ""
        supplier_name = ""
        supplier_email = ""
        worker_emails = set()

        first_wl = worklogs[0]
        if first_wl.project_id:
            row = db.execute(text("SELECT name FROM projects WHERE id=:pid"), {"pid": first_wl.project_id}).first()
            if row:
                project_name = row[0] or ""

        if first_wl.work_order_id:
            row = db.execute(text(
                "SELECT s.name, s.email FROM work_orders wo JOIN suppliers s ON wo.supplier_id=s.id WHERE wo.id=:wid"
            ), {"wid": first_wl.work_order_id}).first()
            if row:
                supplier_name, supplier_email = row[0] or "", row[1] or ""

        for wl in worklogs:
            if wl.user_id:
                row = db.execute(text("SELECT email FROM users WHERE id=:uid AND email IS NOT NULL"),
                                 {"uid": wl.user_id}).first()
                if row and row[0]:
                    worker_emails.add(row[0])

        body = (
            f"שלום,\n\n"
            f"חשבונית {invoice_number} הופקה.\n"
            f"פרויקט: {project_name}\n"
            f"ספק: {supplier_name}\n"
            f"סה\"כ: {total_amount:,.0f}\n"
            f"תאריך: {invoice_date}\n\n"
            "Forewise"
        )

        subject = f"חשבונית {invoice_number} הופקה — {project_name}"

        if supplier_email:
            send_email(to=supplier_email, subject=subject, body=body)

        for email in worker_emails:
            send_email(to=email, subject=subject, body=body)

    except Exception as e:
        log.warning(f"Worklog Stage 3 (invoiced) email failed: {e}")
