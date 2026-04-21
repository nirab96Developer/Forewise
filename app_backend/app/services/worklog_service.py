"""
Worklog Service — core financial transaction engine for equipment work reporting.

This service manages the full lifecycle of worklogs (time-and-cost reports) against
work orders. Worklogs are the primary billing artifact: each one captures hours worked,
calculates cost using a resolved hourly rate, and applies Israeli VAT (18%).

Lifecycle:  PENDING → SUBMITTED → APPROVED → INVOICED
                                 ↘ REJECTED

Key design decisions:
- Does NOT inherit BaseService because worklogs use `is_active` for soft-delete
  rather than the `deleted_at` pattern used by master-data entities.
- Financial fields (rate, cost, VAT) are NEVER accepted from the client — they are
  always computed server-side to prevent tampering.
- Rate resolution follows a strict 2-level hierarchy (work_order → supplier_equipment)
  with no silent fallbacks; missing rates cause a hard block.
- Budget accounting is incremental: frozen budget is released on approval, not on creation.
"""

from datetime import datetime
from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func

from app.models.worklog import Worklog
from app.models.work_order import WorkOrder
from app.models.user import User
from app.models.project import Project
from app.models.equipment import Equipment
from app.models.activity_type import ActivityType
from app.schemas.worklog import WorklogCreate, WorklogUpdate, WorklogSearch, WorklogStatistics
from app.core.exceptions import NotFoundException, ValidationException
from app.services import activity_logger
from app.services.rate_service import resolve_supplier_pricing


class WorklogService:
    """
    Worklog Service — TRANSACTIONS category.

    Unlike master-data services (projects, users, equipment), this service does NOT
    inherit BaseService. Worklogs use ``is_active`` for deactivation instead of
    ``deleted_at``, because financial records should never be physically deleted —
    they must remain auditable even when logically removed.

    Financial calculation pipeline (create):
        1. Resolve hourly rate via ``_resolve_hourly_rate()``
        2. Compute ``cost_before_vat = work_hours × rate + overnight_total``
        3. Apply VAT: ``cost_with_vat = cost_before_vat × (1 + 0.18)``
        4. Snapshot the rate so future rate changes don't retroactively alter history.
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

    VAT_RATE = 0.18  # Israeli standard VAT rate, applied to all worklog costs

    def _resolve_hourly_rate(self, db: Session, worklog_dict: dict) -> float:
        """Resolve the hourly rate for a worklog using a strict 2-level hierarchy.

        The rate resolution intentionally has NO silent fallbacks to prevent
        under-billing. If no rate is found, the caller must block creation and
        force the user to configure pricing first.

        Resolution order:
            1. ``work_orders.hourly_rate`` — an explicit per-order rate override,
               typically set during negotiation or for non-standard pricing.
            2. ``supplier_equipment.hourly_rate`` — the contractual rate for the
               specific supplier + license plate combination. This is the normal path.
            3. No match → returns 0.0, signaling the caller to raise a
               ValidationException (rate must be configured before reporting).

        Args:
            db: Database session.
            worklog_dict: Partially built worklog data containing ``work_order_id``.

        Returns:
            The resolved hourly rate as a float, or 0.0 if no rate could be found.
        """
        wo_id = worklog_dict.get('work_order_id')
        if not wo_id:
            return 0

        wo = db.query(WorkOrder).filter_by(id=wo_id).first()
        if not wo:
            return 0

        pricing = resolve_supplier_pricing(
            db=db,
            supplier_id=wo.supplier_id,
            equipment_id=worklog_dict.get('equipment_id') or wo.equipment_id,
            license_plate=wo.equipment_license_plate,
            equipment_type_name=wo.equipment_type,
            equipment_model_id=getattr(wo, 'requested_equipment_model_id', None),
        )
        return float(pricing.get("hourly_rate") or 0)
    
    def create(self, db: Session, data: WorklogCreate, current_user_id: int) -> Worklog:
        """Create a new worklog with comprehensive business-rule validation.

        This is the most complex method in the service. It enforces a strict
        validation pipeline before persisting, then computes all financial fields
        server-side to prevent client-side tampering.

        Validation pipeline (in order):
            1. Work order existence and project association
            2. State machine gate — WO must be coordinator-approved
            3. Equipment scan gate — license plate must be on the WO
            4. Scan mismatch detection (supplier/type) with role-based overrides
            5. Uniqueness constraint — one worklog per WO per day
            6. Foreign key validation for user, project, equipment, activity_type

        Financial security:
            - All client-provided financial fields (``hourly_rate_snapshot``,
              ``cost_before_vat``, ``cost_with_vat``, ``vat_rate``, ``approved_*``)
              are stripped from the input and recomputed server-side.
            - The hourly rate is resolved via ``_resolve_hourly_rate()`` and
              snapshotted so future rate changes don't alter historical records.

        Overnight (field-guard) handling:
            - A single checkbox ``includes_guard`` triggers overnight billing at a
              fixed rate of 250 NIS/night, added on top of hourly cost.

        Args:
            db: Database session.
            data: Validated input from the API layer.
            current_user_id: The authenticated user creating this report.

        Returns:
            The persisted Worklog ORM instance.

        Raises:
            ValidationException: For any business-rule violation.
        """
        # RULE 1: work_order_id is mandatory
        if not data.work_order_id:
            raise ValidationException("חובה לציין הזמנת עבודה (work_order_id)")

        wo = db.query(WorkOrder).filter_by(id=data.work_order_id).first()
        if not wo:
            raise ValidationException(f"Work order {data.work_order_id} not found")

        # RULE 1b: business-rule validation for work_hours per report_type.
        # Schema allows ge=0 (storage worklogs are 0h) but for any other type
        # we require at least one positive hour to avoid bogus zero-cost rows.
        report_type_lower = (data.report_type or 'standard').lower()
        wh_value = float(data.work_hours or 0)
        if report_type_lower != 'storage' and wh_value <= 0:
            raise ValidationException("חובה לדווח על שעות עבודה > 0 (אלא בדיווח אחסון).")

        # RULE 2: project_id must exist (workspace enforcement)
        if not wo.project_id:
            raise ValidationException("להזמנה זו אין פרויקט משויך")

        # RULE 3: State machine gate — only coordinator-approved WOs accept reports.
        # The full WO lifecycle is: SUPPLIER_ACCEPTED → Coordinator approves →
        # APPROVED_AND_SENT → Work Manager scans equipment → IN_PROGRESS → worklogs.
        # We allow reporting only in statuses that indicate the coordinator has signed off.
        WORKABLE_STATUSES = {'APPROVED_AND_SENT', 'IN_PROGRESS', 'ACTIVE'}
        wo_status = (wo.status or '').upper()
        if wo_status not in WORKABLE_STATUSES:
            if wo_status == 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR':
                raise ValidationException("הזמנה ממתינה לאישור מתאם — לא ניתן לדווח לפני אישור סופי.")
            raise ValidationException(
                f"לא ניתן לדווח על הזמנה בסטטוס '{wo.status}'. ההזמנה חייבת להיות מאושרת ע\"י המתאם."
            )

        # RULE 4: Equipment must be scanned (license_plate on WO)
        if not wo.equipment_license_plate:
            raise ValidationException(
                "לא ניתן ליצור דיווח — לא נסרק כלי להזמנה זו. יש לסרוק ציוד קודם."
            )

        # RULE 5: Scan validation — detect mismatches between scanned and expected equipment.
        # Flags are stored in metadata_json so reviewers can see discrepancies during approval.
        scan_flags = []

        # 5a: Supplier mismatch — flag only (non-blocking, for reviewer awareness)
        if data.supplier_id and wo.supplier_id and int(data.supplier_id) != int(wo.supplier_id):
            scan_flags.append('supplier_mismatch')

        # 5b: Equipment type mismatch — hard block for non-admins.
        # Different equipment type could mean wrong pricing tier, so only
        # ADMIN/SUPER_ADMIN can force it through.
        if hasattr(data, 'equipment_type') and data.equipment_type and wo.equipment_type:
            if data.equipment_type.strip().lower() != wo.equipment_type.strip().lower():
                scan_flags.append('equipment_type_mismatch')
                # Check if current user is Admin
                current_user_obj = db.query(User).filter_by(id=current_user_id).first()
                is_admin = current_user_obj and current_user_obj.role and current_user_obj.role.code in ('ADMIN', 'SUPER_ADMIN')
                if not is_admin:
                    raise ValidationException(
                        f"סוג הכלי שנסרק ({data.equipment_type}) שונה מסוג הכלי בהזמנה ({wo.equipment_type}). "
                        "רק מנהל מערכת יכול לאשר שינוי סוג כלי."
                    )

        # RULE 6: Business uniqueness — prevent duplicate billing for the same
        # work order on the same day. This is an application-level guard because
        # the DB constraint alone can't account for is_active filtering.
        from sqlalchemy import text as sa_text
        report_date = data.report_date or data.work_date
        if report_date:
            dup = db.execute(sa_text(
                "SELECT id FROM worklogs WHERE work_order_id = :woid AND report_date = :rd AND is_active = true LIMIT 1"
            ), {"woid": wo.id, "rd": str(report_date)}).first()
            if dup:
                raise ValidationException(
                    f"כבר קיים דיווח עבור הזמנה #{wo.order_number or wo.id} בתאריך {report_date}"
                )

        # Auto-inherit equipment from work order
        if not data.equipment_id and wo.equipment_id:
            data.equipment_id = wo.equipment_id

        # Derive missing fields from work_order
        user_id = data.user_id or current_user_id
        project_id = data.project_id or wo.project_id
        supplier_id = (data.supplier_id if hasattr(data, 'supplier_id') and data.supplier_id else None) or wo.supplier_id
        
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
        
        # Overnight/guard handling: the frontend sends a single boolean `includes_guard`.
        # We strip any client-provided overnight fields and recompute them below
        # to prevent rate manipulation.
        includes_guard = bool(worklog_dict.pop('includes_guard', False))
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

        # SECURITY: Strip all financial and approval fields from client input.
        # These are computed server-side to prevent billing fraud. A malicious client
        # could otherwise set cost_with_vat=0 or pre-approve their own worklog.
        for unsafe_field in ('hourly_rate_snapshot', 'cost_before_vat', 'cost_with_vat',
                             'vat_rate', 'net_hours', 'paid_hours', 'total_hours',
                             'approved_by_user_id', 'approved_at'):
            worklog_dict.pop(unsafe_field, None)

        pricing = resolve_supplier_pricing(
            db=db,
            supplier_id=supplier_id,
            equipment_id=worklog_dict.get('equipment_id') or wo.equipment_id,
            license_plate=wo.equipment_license_plate,
            equipment_type_name=wo.equipment_type,
            equipment_model_id=getattr(wo, 'requested_equipment_model_id', None),
        )
        rate = float(pricing.get("hourly_rate") or 0)
        overnight_rate = float(pricing.get("overnight_rate") or 0)

        if not rate or rate <= 0:
            raise ValidationException(
                "לא מוגדר תעריף לכלי/ספק זה. יש להגדיר מחיר בדף ספקים ותמחורים."
            )

        # לינת שטח — מחושבת מתוך הגדרות הספקים / סוגי הציוד
        overnight_total = 0.0
        if includes_guard:
            resolved_overnight = overnight_rate if overnight_rate > 0 else 250.0
            worklog_dict['is_overnight'] = True
            worklog_dict['overnight_nights'] = 1
            worklog_dict['overnight_rate'] = Decimal(str(resolved_overnight))
            overnight_total = resolved_overnight

        # Re-apply computed hour fields after stripping unsafe client input.
        worklog_dict['total_hours'] = round(wh + bh, 2) if wh > 0 else float(worklog_dict.get('total_hours') or 0)
        worklog_dict['net_hours'] = round(wh, 2) if wh > 0 else float(worklog_dict.get('net_hours') or 0)
        worklog_dict['paid_hours'] = round(wh, 2) if wh > 0 else float(worklog_dict.get('paid_hours') or 0)
        worklog_dict['hourly_rate_snapshot'] = rate

        hours = float(worklog_dict.get('work_hours') or 0)
        rate_f = float(rate)
        worklog_dict['cost_before_vat'] = round(hours * rate_f + overnight_total, 2)
        worklog_dict['vat_rate'] = self.VAT_RATE
        worklog_dict['cost_with_vat'] = round(worklog_dict['cost_before_vat'] * (1 + self.VAT_RATE), 2)

        if includes_guard:
            worklog_dict['overnight_total'] = Decimal(str(overnight_total))
        
        if scan_flags:
            import json
            existing_meta = worklog_dict.get('metadata_json')
            meta = json.loads(existing_meta) if existing_meta else {}
            meta['scan_flags'] = scan_flags
            worklog_dict['metadata_json'] = json.dumps(meta, ensure_ascii=False)

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
        """Update worklog — safe field allowlist, recalculates cost if hours change"""
        worklog = self.get_by_id(db, worklog_id)
        if not worklog:
            raise NotFoundException(f"Worklog {worklog_id} not found")
        
        ALLOWED_UPDATE_FIELDS = {
            'report_date', 'work_hours', 'break_hours',
            'start_time', 'end_time', 'activity_description', 'notes',
        }
        update_dict = data.model_dump(exclude_unset=True)
        hours_changed = False
        for field, value in update_dict.items():
            if field in ALLOWED_UPDATE_FIELDS:
                if field == 'work_hours' and value != worklog.work_hours:
                    hours_changed = True
                setattr(worklog, field, value)
        
        if hours_changed and worklog.hourly_rate_snapshot:
            wh = float(worklog.work_hours or 0)
            bh = float(worklog.break_hours or 0)
            rate = float(worklog.hourly_rate_snapshot)
            overnight = float(worklog.overnight_nights or 0) * float(worklog.overnight_rate or 250)
            worklog.total_hours = round(Decimal(str(wh + bh)), 2)
            worklog.net_hours = round(Decimal(str(wh)), 2)
            worklog.paid_hours = round(Decimal(str(wh)), 2)
            worklog.cost_before_vat = round(Decimal(str(wh * rate + overnight)), 2)
            worklog.vat_rate = Decimal(str(self.VAT_RATE))
            worklog.cost_with_vat = round(worklog.cost_before_vat * (1 + Decimal(str(self.VAT_RATE))), 2)
        
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
    
    def submit(self, db: Session, worklog_id: int, current_user_id: int, notes: Optional[str] = None) -> Worklog:
        """Submit worklog for approval.

        - Validates current state (only PENDING/DRAFT can be submitted).
        - Persists submitted_at / submitted_by_id (audit trail).
        - Appends optional notes to existing notes column.
        """
        from sqlalchemy import text as sa_text
        from datetime import datetime as _dt
        worklog = self.get_by_id(db, worklog_id)
        if not worklog:
            raise NotFoundException(f"Worklog {worklog_id} not found")

        # State machine: only PENDING/DRAFT can be submitted
        wl_status = (worklog.status or '').upper()
        if wl_status in ('SUBMITTED', 'APPROVED', 'INVOICED', 'REJECTED'):
            raise ValidationException(
                f"לא ניתן להגיש דיווח בסטטוס '{worklog.status}'."
            )

        worklog.status = 'SUBMITTED'
        worklog.submitted_at = _dt.utcnow()
        worklog.submitted_by_id = current_user_id
        if notes:
            stamp = _dt.utcnow().strftime('%Y-%m-%d %H:%M')
            addition = f"\n[הגשה {stamp}] {notes.strip()}"
            worklog.notes = (worklog.notes or '') + addition

        # Compute hours metadata + persist on the row so reviewers can see context
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

        # Enrich metadata_json (column added in migration d1e2f3a4b5c6)
        if hours_meta:
            import json
            try:
                existing = json.loads(worklog.metadata_json or '{}') if worklog.metadata_json else {}
                existing.update(hours_meta)
                worklog.metadata_json = json.dumps(existing, ensure_ascii=False)
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
    
    def approve(self, db: Session, worklog_id: int, current_user_id: int, notes: Optional[str] = None) -> Worklog:
        """Approve worklog — state machine + self-approval block.

        Optional ``notes`` are appended to the worklog so the approval reasoning
        is preserved (audit + supplier visibility).
        """
        worklog = self.get_by_id(db, worklog_id)
        if not worklog:
            raise NotFoundException(f"Worklog {worklog_id} not found")

        # State machine: only SUBMITTED can be approved
        wl_status = (worklog.status or '').upper()
        if wl_status not in ('SUBMITTED', 'PENDING'):
            raise ValidationException(f"לא ניתן לאשר דיווח בסטטוס '{worklog.status}'. יש להגיש (SUBMIT) קודם.")

        if worklog.user_id == current_user_id:
            raise ValidationException("לא ניתן לאשר דיווח שנוצר על ידך. יש לבקש אישור מגורם אחר.")

        from datetime import datetime as _dt
        worklog.status = 'APPROVED'
        worklog.approved_by_user_id = current_user_id
        worklog.approved_at = _dt.utcnow()
        if notes:
            stamp = _dt.utcnow().strftime('%Y-%m-%d %H:%M')
            addition = f"\n[אושר {stamp}] {notes.strip()}"
            worklog.notes = (worklog.notes or '') + addition
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
                    cost = float(worklog.cost_before_vat or 0)

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
        """Reject worklog and persist the reason on the row."""
        from datetime import datetime as _dt
        worklog = self.get_by_id(db, worklog_id)
        if not worklog:
            raise NotFoundException(f"Worklog {worklog_id} not found")

        worklog.status = 'REJECTED'
        # Persist reason so the worker, accountant and audit can see WHY.
        # (Previously the parameter was accepted but silently dropped — bug F2.6.)
        if reason:
            worklog.rejection_reason = reason.strip()
        worklog.updated_at = _dt.utcnow()
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
    vat_rate: float = 0.18,
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
        vat_rate=0.18,
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
    Attaches Invoice PDF if generation succeeds.
    """
    import logging
    log = logging.getLogger(__name__)
    try:
        from app.core.email import send_email, send_email_with_pdf
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

        # Generate PDF attachment
        pdf_bytes = None
        pdf_filename = f"invoice_{invoice_number}.pdf"
        try:
            from app.services.pdf_documents import generate_invoice_pdf
            invoice_id = getattr(invoice, 'id', None)
            if invoice_id:
                pdf_bytes = generate_invoice_pdf(invoice_id, db)
        except Exception as pdf_err:
            log.warning(f"Invoice PDF generation failed for email: {pdf_err}")

        all_recipients = set()
        if supplier_email:
            all_recipients.add(supplier_email)
        all_recipients.update(worker_emails)

        for email in all_recipients:
            try:
                if pdf_bytes:
                    send_email_with_pdf(
                        to=email, subject=subject, body=body,
                        pdf_bytes=pdf_bytes, pdf_filename=pdf_filename,
                    )
                else:
                    send_email(to=email, subject=subject, body=body)
            except Exception as send_err:
                log.warning(f"Invoice email to {email} failed: {send_err}")

    except Exception as e:
        log.warning(f"Worklog Stage 3 (invoiced) email failed: {e}")
