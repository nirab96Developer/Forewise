# app/services/work_order_service.py
"""Work order management service."""
import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.models.work_order import WorkOrder
from app.models.supplier import Supplier
from app.models.project import Project
from app.schemas.work_order import WorkOrderCreate, WorkOrderUpdate, WorkOrderResponse


class WorkOrderService:
    """Service for work order operations."""

    def get_work_order(self, db: Session, work_order_id: int) -> Optional[WorkOrder]:
        """Get work order by ID with relationships."""
        return (
            db.query(WorkOrder)
            .options(
                joinedload(WorkOrder.project),
                joinedload(WorkOrder.supplier)
            )
            .filter(WorkOrder.id == work_order_id)
            .first()
        )

    def get_work_orders(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        project_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        status: Optional[str] = None,
        equipment_type: Optional[str] = None,
    ) -> List[WorkOrder]:
        """Get list of work orders with filters — excludes soft-deleted."""
        query = db.query(WorkOrder).filter(
            WorkOrder.deleted_at.is_(None),
            WorkOrder.is_active.is_(True),
        )

        if project_id:
            query = query.filter(WorkOrder.project_id == project_id)
        if supplier_id:
            query = query.filter(WorkOrder.supplier_id == supplier_id)
        if status:
            query = query.filter(WorkOrder.status == status)
        if equipment_type:
            query = query.filter(WorkOrder.equipment_type == equipment_type)

        return query.offset(skip).limit(limit).all()

    def create_work_order(
        self, db: Session, work_order: WorkOrderCreate, created_by_id: int
    ) -> WorkOrder:
        """Create new work order."""
        from sqlalchemy import text as sa_text
        from fastapi import HTTPException

        # Generate portal token
        portal_token = secrets.token_urlsafe(32)
        token_expires_at = datetime.utcnow() + timedelta(hours=3)

        # Build dict, exclude None values and auto-generated fields
        wo_dict = {k: v for k, v in work_order.dict().items()
                   if v is not None and k not in ("order_number",)}
        # Normalize status to UPPERCASE
        wo_dict['status'] = (wo_dict.get('status') or 'PENDING').upper()

        # ── Auto-resolve requested_equipment_model_id from equipment_type name ──
        # FK constraint fk_work_orders_req_model requires a valid equipment_models.id
        if not wo_dict.get("requested_equipment_model_id"):
            equipment_type_name = (wo_dict.get("equipment_type") or "").strip()
            if not equipment_type_name:
                raise HTTPException(
                    status_code=400,
                    detail="חובה לציין סוג כלי (equipment_type)"
                )

            # Step 1: find category by exact name match
            cat_row = db.execute(sa_text(
                "SELECT id FROM equipment_categories WHERE name = :n AND deleted_at IS NULL LIMIT 1"
            ), {"n": equipment_type_name}).fetchone()

            if not cat_row:
                raise HTTPException(
                    status_code=400,
                    detail=f"סוג כלי לא קיים במערכת: '{equipment_type_name}'"
                )
            cat_id = cat_row[0]

            # Step 2: find default model for that category
            model_row = db.execute(sa_text(
                "SELECT id FROM equipment_models WHERE category_id = :c AND deleted_at IS NULL ORDER BY id LIMIT 1"
            ), {"c": cat_id}).fetchone()
            if not model_row:
                raise HTTPException(
                    status_code=400,
                    detail=f"לא נמצא דגם ציוד לקטגוריה: '{equipment_type_name}'"
                )
            wo_dict["requested_equipment_model_id"] = model_row[0]

        # ── Budget validation: block if project budget insufficient ──────────────
        project_id = wo_dict.get("project_id")
        estimated_hours = wo_dict.get("estimated_hours")
        if project_id and estimated_hours:
            try:
                from app.models.budget import Budget
                from decimal import Decimal as _Decimal

                budget = (
                    db.query(Budget)
                    .filter(
                        Budget.project_id == project_id,
                        Budget.is_active.is_(True),
                        Budget.deleted_at.is_(None),
                    )
                    .first()
                )
                if budget is not None:
                    # Estimate cost using equipment hourly rate from the category
                    rate_row = db.execute(sa_text(
                        """SELECT et.default_hourly_rate
                           FROM equipment_categories ec
                           JOIN equipment_models em ON em.category_id = ec.id
                           JOIN equipment_types et ON et.name = ec.name
                           WHERE em.id = :mid LIMIT 1"""
                    ), {"mid": wo_dict.get("requested_equipment_model_id")}).fetchone()

                    if rate_row and rate_row[0]:
                        estimated_cost = _Decimal(str(estimated_hours)) * _Decimal(str(rate_row[0]))
                        remaining = budget.remaining_amount
                        if estimated_cost > remaining:
                            raise HTTPException(
                                status_code=422,
                                detail={
                                    "code": "BUDGET_INSUFFICIENT",
                                    "message": "תקציב הפרויקט אינו מספיק ליצירת הזמנת העבודה",
                                    "estimated_cost": float(estimated_cost),
                                    "remaining_budget": float(remaining),
                                    "currency": "ILS",
                                }
                            )
            except HTTPException:
                raise
            except Exception:
                pass  # budget check is advisory — do not block on unexpected errors

        # Auto-generate order_number
        max_on = db.execute(sa_text("SELECT COALESCE(MAX(order_number), 0) FROM work_orders")).scalar()
        next_on = int(max_on) + 1

        db_work_order = WorkOrder(
            **wo_dict,
            order_number=next_on,
            created_by_id=created_by_id,
            created_at=datetime.utcnow(),
            portal_token=portal_token,
            token_expires_at=token_expires_at,
        )
        
        db.add(db_work_order)
        db.commit()
        db.refresh(db_work_order)
        return db_work_order

    def update_work_order(
        self, db: Session, work_order_id: int, work_order: WorkOrderUpdate
    ) -> Optional[WorkOrder]:
        """Update work order."""
        db_work_order = self.get_work_order(db, work_order_id)
        if not db_work_order:
            return None

        update_data = work_order.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_work_order, field, value)

        db_work_order.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_work_order)
        return db_work_order

    def delete_work_order(self, db: Session, work_order_id: int) -> bool:
        """Soft delete work order — sets is_active=False and deleted_at."""
        db_work_order = self.get_work_order(db, work_order_id)
        if not db_work_order:
            return False

        db_work_order.is_active = False
        db_work_order.updated_at = datetime.utcnow()
        if hasattr(db_work_order, 'deleted_at'):
            db_work_order.deleted_at = datetime.utcnow()
        db.commit()
        return True

    def send_to_supplier(self, db: Session, work_order_id: int, current_user_id: int = None) -> dict:
        """
        Send work order to supplier — generates portal token and sends email.
        If no supplier is assigned, uses Fair Rotation to select one.
        Returns dict with { work_order, portal_token, portal_url, expires_at }.
        """
        import secrets
        from datetime import timedelta
        from app.core.config import settings

        work_order = self.get_work_order(db, work_order_id)
        if not work_order:
            from app.core.exceptions import NotFoundException
            raise NotFoundException(f"Work order {work_order_id} not found")

        allowed = {'pending', 'PENDING', 'DISTRIBUTING', 'distributing', 'draft', 'DRAFT'}
        if work_order.status not in allowed:
            from app.core.exceptions import ValidationException
            raise ValidationException(
                f"Work order must be in PENDING status to send to supplier (current: {work_order.status})"
            )

        # If no supplier assigned, use Fair Rotation to find one
        if not work_order.supplier_id:
            selected_supplier_id = self._select_supplier_by_rotation(db, work_order)
            if not selected_supplier_id:
                from app.core.exceptions import ValidationException
                raise ValidationException(
                    "לא נמצא ספק זמין עבור הזמנה זו. "
                    "ודא שקיימים ספקים פעילים עם הציוד המתאים."
                )
            work_order.supplier_id = selected_supplier_id

        # Generate portal token valid for 3 hours
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=3)
        portal_url = f"https://forewise.co/supplier-portal/{token}"

        work_order.portal_token = token
        work_order.portal_expiry = expires_at
        work_order.status = "DISTRIBUTING"
        work_order.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(work_order)

        # Send email to supplier
        email_sent = False
        supplier_name = "ספק"
        try:
            from app.models.supplier import Supplier
            supplier = db.query(Supplier).filter(Supplier.id == work_order.supplier_id).first()
            if supplier:
                supplier_name = supplier.name
                to_email = supplier.email or supplier.contact_email
                if to_email:
                    from app.core.email import send_email
                    send_email(
                        to=to_email,
                        subject=f"הזמנת עבודה מספר {work_order.order_number} - דורש תגובה",
                        body=(
                            f"שלום {supplier.name},\n\n"
                            f"קיבלת הזמנת עבודה חדשה מForewise.\n"
                            f"הזמנה: {work_order.title or work_order.order_number}\n\n"
                            f"לצפייה ואישור/דחייה:\n{portal_url}\n\n"
                            f"הקישור תקף עד: {expires_at.strftime('%d/%m/%Y %H:%M')}\n\n"
                            "Forewise"
                        ),
                    )
                    email_sent = True
                else:
                    import logging
                    logging.getLogger(__name__).warning(
                        f"Supplier {supplier.id} ({supplier.name}) has no email address"
                    )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to send portal email: {e}")

        return {
            "work_order": work_order,
            "portal_token": token,
            "portal_url": portal_url,
            "expires_at": expires_at.isoformat(),
            "email_sent": email_sent,
            "supplier_name": supplier_name,
        }

    def _select_supplier_by_rotation(self, db: Session, work_order) -> Optional[int]:
        """Select supplier using Fair Rotation algorithm."""
        from app.models.supplier_rotation import SupplierRotation
        from app.models.supplier import Supplier

        # Get project's area for geographic filtering
        area_id = None
        if work_order.project_id:
            from app.models.project import Project
            project = db.query(Project).filter(Project.id == work_order.project_id).first()
            if project:
                area_id = project.area_id

        # Find eligible suppliers with matching equipment
        query = (
            db.query(SupplierRotation)
            .join(Supplier, Supplier.id == SupplierRotation.supplier_id)
            .filter(
                SupplierRotation.is_active == True,
                SupplierRotation.is_available != False,
                Supplier.is_active == True,
            )
        )

        # Filter by equipment type if work order has one
        eq_type_id = getattr(work_order, 'equipment_type_id', None)
        if not eq_type_id and work_order.equipment_id:
            from app.models.equipment import Equipment
            eq = db.query(Equipment).filter(Equipment.id == work_order.equipment_id).first()
            if eq:
                eq_type_id = getattr(eq, 'type_id', None) or getattr(eq, 'equipment_type_id', None)
        if eq_type_id:
            query = query.filter(
                SupplierRotation.equipment_type_id == eq_type_id
            )

        # Prefer same area
        if area_id:
            area_query = query.filter(SupplierRotation.area_id == area_id)
            rotations = area_query.order_by(SupplierRotation.rotation_position.asc()).all()
            if not rotations:
                rotations = query.order_by(SupplierRotation.rotation_position.asc()).all()
        else:
            rotations = query.order_by(SupplierRotation.rotation_position.asc()).all()

        if not rotations:
            # Fallback: any active supplier
            fallback = db.query(Supplier).filter(Supplier.is_active == True).first()
            return fallback.id if fallback else None

        # Pick the one with lowest rotation_position (next in line)
        selected = rotations[0]

        # Update rotation position
        selected.total_assignments = (selected.total_assignments or 0) + 1
        selected.last_assignment_date = datetime.utcnow().date()
        if selected.rotation_position is not None:
            selected.rotation_position += 1

        db.flush()
        return selected.supplier_id

    def handle_supplier_response(
        self, db: Session, portal_token: str, response: str, reason: Optional[str] = None
    ) -> Optional[WorkOrder]:
        """Handle supplier response to work order."""
        work_order = (
            db.query(WorkOrder)
            .filter(
                and_(
                    WorkOrder.portal_token == portal_token,
                    WorkOrder.status == "sent_to_supplier",
                    WorkOrder.token_expires_at > datetime.utcnow()
                )
            )
            .first()
        )

        if not work_order:
            return None

        if response.lower() == "accept":
            work_order.status = "accepted"
        elif response.lower() == "reject":
            work_order.status = "rejected"
        else:
            raise ValueError("Response must be 'accept' or 'reject'")

        work_order.responded_at = datetime.utcnow()
        work_order.updated_at = datetime.utcnow()
        
        if reason:
            work_order.notes = reason

        db.commit()
        db.refresh(work_order)
        return work_order

    def force_supplier(
        self, db: Session, work_order_id: int, supplier_id: int, reason: str
    ) -> Optional[WorkOrder]:
        """Force work order to specific supplier."""
        work_order = self.get_work_order(db, work_order_id)
        if not work_order:
            return None

        # Validate supplier exists
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise ValueError("Supplier not found")

        # Update work order
        work_order.supplier_id = supplier_id
        work_order.is_forced = True
        work_order.force_reason = reason
        work_order.updated_at = datetime.utcnow()

        # Generate new portal token
        work_order.portal_token = secrets.token_urlsafe(32)
        work_order.token_expires_at = datetime.utcnow() + timedelta(hours=3)
        work_order.status = "sent_to_supplier"
        work_order.sent_at = datetime.utcnow()

        db.commit()
        db.refresh(work_order)
        return work_order

    def start_work(self, db: Session, work_order_id: int) -> Optional[WorkOrder]:
        """Start work on work order."""
        work_order = self.get_work_order(db, work_order_id)
        if not work_order:
            return None

        if work_order.status != "accepted":
            raise ValueError("Work order must be accepted to start work")

        work_order.status = "in_progress"
        work_order.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(work_order)
        return work_order

    def complete_work(
        self, db: Session, work_order_id: int, actual_hours: Optional[float] = None
    ) -> Optional[WorkOrder]:
        """Complete work order."""
        work_order = self.get_work_order(db, work_order_id)
        if not work_order:
            return None

        if work_order.status != "in_progress":
            raise ValueError("Work order must be in progress to complete")

        work_order.status = "completed"
        work_order.completed_at = datetime.utcnow()
        work_order.updated_at = datetime.utcnow()
        
        if actual_hours:
            work_order.actual_hours = actual_hours

        db.commit()
        db.refresh(work_order)
        return work_order

    def expire_work_orders(self, db: Session) -> List[WorkOrder]:
        """Expire work orders that haven't been responded to (scheduled task)."""
        expired_orders = (
            db.query(WorkOrder)
            .filter(
                and_(
                    WorkOrder.status == "sent_to_supplier",
                    WorkOrder.token_expires_at < datetime.utcnow()
                )
            )
            .all()
        )

        for order in expired_orders:
            order.status = "expired"
            order.updated_at = datetime.utcnow()

        db.commit()
        return expired_orders

    def get_supplier_portal_view(self, db: Session, portal_token: str) -> Optional[dict]:
        """Get work order view for supplier portal."""
        work_order = (
            db.query(WorkOrder)
            .options(
                joinedload(WorkOrder.project),
                joinedload(WorkOrder.supplier)
            )
            .filter(
                and_(
                    WorkOrder.portal_token == portal_token,
                    WorkOrder.status == "sent_to_supplier",
                    WorkOrder.token_expires_at > datetime.utcnow()
                )
            )
            .first()
        )

        if not work_order:
            return None

        return {
            "order_number": f"WO-{work_order.id:06d}",
            "title": work_order.title,
            "description": work_order.description,
            "equipment_type": work_order.equipment_type,
            "equipment_count": work_order.equipment_count,
            "start_date": work_order.start_date,
            "end_date": work_order.end_date,
            "hourly_rate": work_order.hourly_rate,
            "estimated_hours": work_order.estimated_hours,
            "location": work_order.project.location_name if work_order.project else None,
            "contact_person": work_order.supplier.contact_person if work_order.supplier else None,
            "contact_phone": work_order.supplier.phone if work_order.supplier else None,
            "contact_email": work_order.supplier.email if work_order.supplier else None,
            "portal_token": work_order.portal_token,
            "expires_at": work_order.token_expires_at,
            "is_forced": work_order.is_forced,
            "force_reason": work_order.force_reason,
        }

    def get_work_order_statistics(self, db: Session, project_id: Optional[int] = None) -> dict:
        """Get work order statistics."""
        query = db.query(WorkOrder)
        
        if project_id:
            query = query.filter(WorkOrder.project_id == project_id)

        total_orders = query.count()
        
        # Count by status
        status_counts = {}
        for status in ["pending", "sent_to_supplier", "accepted", "rejected", 
                      "in_progress", "completed", "cancelled", "expired"]:
            count = query.filter(WorkOrder.status == status).count()
            status_counts[f"{status}_count"] = count

        # Financial statistics
        from sqlalchemy import func
        total_estimated_cost = query.with_entities(
            func.sum(WorkOrder.hourly_rate * WorkOrder.estimated_hours)
        ).scalar() or 0

        total_actual_cost = query.with_entities(
            func.sum(WorkOrder.hourly_rate * WorkOrder.actual_hours)
        ).scalar() or 0

        avg_hourly_rate = query.with_entities(
            func.avg(WorkOrder.hourly_rate)
        ).scalar() or 0

        return {
            "total_orders": total_orders,
            **status_counts,
            "total_estimated_cost": total_estimated_cost,
            "total_actual_cost": total_actual_cost,
            "average_hourly_rate": avg_hourly_rate,
        }

    # ── Alias/bridge methods for router compatibility ────────────
    def list(self, db, search=None, current_user=None):
        """List work orders with enriched data (supplier, project, area, region names)."""
        from sqlalchemy import text as sa_text

        # Build base filters
        status_filter = ""
        area_filter = ""
        project_filter = ""
        supplier_filter = ""
        params: dict = {}

        if search:
            if getattr(search, 'status', None):
                status_filter = "AND wo.status = :status"
                params['status'] = search.status
            if getattr(search, 'area_id', None):
                area_filter = "AND a.id = :area_id"
                params['area_id'] = search.area_id
            if getattr(search, 'project_id', None):
                project_filter = "AND wo.project_id = :project_id"
                params['project_id'] = search.project_id
            if getattr(search, 'supplier_id', None):
                supplier_filter = "AND wo.supplier_id = :supplier_id"
                params['supplier_id'] = search.supplier_id

        page = getattr(search, 'page', 1) or 1
        page_size = getattr(search, 'page_size', None) or getattr(search, 'per_page', 50) or 50
        offset = (page - 1) * page_size
        params['limit'] = page_size
        params['offset'] = offset

        sql = sa_text(f"""
            SELECT
                wo.*,
                s.name  AS supplier_name,
                p.name  AS project_name,
                a.name  AS area_name,
                r.name  AS region_name
            FROM work_orders wo
            LEFT JOIN suppliers s  ON s.id = wo.supplier_id
            LEFT JOIN projects  p  ON p.id = wo.project_id
            LEFT JOIN areas     a  ON a.id = p.area_id
            LEFT JOIN regions   r  ON r.id = a.region_id
            WHERE wo.deleted_at IS NULL
              AND wo.is_active = TRUE
              {status_filter}
              {area_filter}
              {project_filter}
              {supplier_filter}
            ORDER BY wo.created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        count_sql = sa_text(f"""
            SELECT COUNT(*)
            FROM work_orders wo
            LEFT JOIN projects p ON p.id = wo.project_id
            LEFT JOIN areas    a ON a.id = p.area_id
            WHERE wo.deleted_at IS NULL
              AND wo.is_active = TRUE
              {status_filter}
              {area_filter}
              {project_filter}
              {supplier_filter}
        """)

        rows = db.execute(sql, params).mappings().all()
        count_params = {k: v for k, v in params.items() if k not in ('limit', 'offset')}
        total = db.execute(count_sql, count_params).scalar() or 0

        # Convert mapping rows to WorkOrder ORM objects augmented with name fields
        wo_ids = [row['id'] for row in rows]
        if not wo_ids:
            return [], total

        orm_map = {
            wo.id: wo
            for wo in db.query(WorkOrder).filter(WorkOrder.id.in_(wo_ids)).all()
        }

        items = []
        for row in rows:
            wo = orm_map.get(row['id'])
            if wo:
                # Set extra name fields as instance attributes (not mapped columns)
                wo.__dict__.setdefault('supplier_name', None)
                wo.__dict__['supplier_name'] = row.get('supplier_name')
                wo.__dict__['project_name'] = row.get('project_name')
                wo.__dict__['area_name'] = row.get('area_name')
                wo.__dict__['region_name'] = row.get('region_name')
                items.append(wo)

        return items, total

    def create(self, db, data, current_user=None, current_user_id=None):
        """Alias → create_work_order()"""
        # create_work_order needs created_by_id (int)
        uid = current_user_id or (current_user.id if hasattr(current_user, 'id') else 1)
        return self.create_work_order(db, data, created_by_id=uid)

    def update(self, db, wo_id, data, current_user_id=None):
        """Alias → update_work_order()"""
        return self.update_work_order(db, wo_id, data)

    def soft_delete(self, db, wo_id, current_user_id=None):
        """Alias → delete_work_order()"""
        return self.delete_work_order(db, wo_id)

    def get_statistics(self, db, current_user=None):
        """Alias → get_work_order_statistics()"""
        return self.get_work_order_statistics(db)

    def get_by_id_or_404(self, db, wo_id):
        """Get work order or raise 404."""
        wo = self.get_work_order(db, wo_id)
        if not wo:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Work order {wo_id} not found")
        return wo

    def restore(self, db, wo_id, current_user_id=None):
        """Restore soft-deleted work order."""
        from app.models.work_order import WorkOrder
        wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
        if wo:
            wo.is_active = True
            db.commit()
            db.refresh(wo)
        return wo

    def approve(self, db, wo_id, request=None, current_user=None, current_user_id=None, notes=None):
        """Approve a work order by coordinator — APPROVED_AND_SENT + emails + notifications."""
        from app.models.work_order import WorkOrder
        import datetime, logging
        log = logging.getLogger(__name__)

        wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
        if not wo:
            return wo

        wo.status = 'APPROVED_AND_SENT'
        wo.updated_at = datetime.datetime.now()
        db.commit()
        db.refresh(wo)

        uid = current_user_id or (current_user.id if current_user else None)
        admin_name = (current_user.full_name or current_user.username) if current_user else 'מתאם'
        order_label = wo.order_number or str(wo_id)

        # ── Activity log ─────────────────────────────────────────────────
        try:
            from sqlalchemy import text
            db.execute(text("""
                INSERT INTO activity_logs (action, description, user_id, entity_type, entity_id)
                VALUES ('WORK_ORDER_APPROVED', :desc, :uid, 'work_order', :wid)
            """), {
                "desc": f"הזמנה מספר {order_label} אושרה לביצוע על ידי {admin_name}",
                "uid": uid,
                "wid": wo_id,
            })
            db.commit()
        except Exception as e:
            log.warning(f"Activity log failed for approve WO {wo_id}: {e}")

        # ── Build location info + Waze link ───────────────────────────────
        location_text = ""
        waze_link = ""
        try:
            if wo.location:
                loc = wo.location
                location_text = loc.name or loc.address or ""
                if loc.address:
                    location_text = f"{loc.name} — {loc.address}" if loc.name else loc.address
                if loc.latitude and loc.longitude:
                    waze_link = f"https://waze.com/ul?ll={loc.latitude},{loc.longitude}&navigate=yes"
            elif wo.location_id:
                from app.models.location import Location
                loc = db.query(Location).filter(Location.id == wo.location_id).first()
                if loc:
                    location_text = loc.address or loc.name or ""
                    if loc.name and loc.address:
                        location_text = f"{loc.name} — {loc.address}"
                    if loc.latitude and loc.longitude:
                        waze_link = f"https://waze.com/ul?ll={loc.latitude},{loc.longitude}&navigate=yes"
        except Exception as e:
            log.warning(f"Failed to build location info for WO {wo_id}: {e}")

        location_line = f"\nמיקום: {location_text}" if location_text else ""
        waze_line = f"\nניווט Waze: {waze_link}" if waze_link else ""

        # ── Email to supplier ─────────────────────────────────────────────
        try:
            if wo.supplier_id:
                from app.models.supplier import Supplier
                supplier = db.query(Supplier).filter(Supplier.id == wo.supplier_id).first()
                if supplier:
                    to_email = supplier.email or supplier.contact_email
                    supplier_name = supplier.name or "ספק"
                    if to_email:
                        from app.core.email import send_email
                        subject = f"הזמנה {order_label} אושרה לביצוע — פרטי מיקום"
                        body = (
                            f"שלום {supplier_name},\n\n"
                            f"הזמנת העבודה מספר {order_label} אושרה סופית על ידי מתאם ההזמנות.\n"
                            f"ניתן לצאת לביצוע."
                            f"{location_line}"
                            f"{waze_line}\n\n"
                            f"לפרטים נוספים יש לפנות למתאם.\n\n"
                            "Forewise"
                        )
                        html_body = f"""
<div dir="rtl" style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:#2d6a2d;color:#fff;padding:20px 24px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;">✅ הזמנה אושרה לביצוע</h2>
  </div>
  <div style="padding:24px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 8px 8px;">
    <p>שלום <strong>{supplier_name}</strong>,</p>
    <p>הזמנת עבודה מספר <strong>{order_label}</strong> אושרה סופית.</p>
    {"<p>📍 <strong>מיקום:</strong> " + location_text + "</p>" if location_text else ""}
    {"<p><a href='" + waze_link + "' style='background:#00b4e8;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;margin-top:8px;'>🧭 נווט ב-Waze</a></p>" if waze_link else ""}
    <hr style="margin:20px 0;border:none;border-top:1px solid #e5e7eb;"/>
    <p style="color:#6b7280;font-size:13px;">לפרטים נוספים יש לפנות למתאם ההזמנות.</p>
    <p style="color:#6b7280;font-size:13px;">Forewise</p>
  </div>
</div>"""
                        send_email(to=to_email, subject=subject, body=body, html_body=html_body)
                        log.info(f"Approval email sent to supplier {to_email} for WO {wo_id}")
        except Exception as e:
            log.warning(f"Failed to send supplier approval email for WO {wo_id}: {e}")

        # ── Email to work order creator (work manager) ────────────────────
        try:
            recipient_user = None
            recipient_label = ""
            if wo.created_by:
                recipient_user = wo.created_by
                recipient_label = wo.created_by.full_name or wo.created_by.username or "מנהל עבודה"
            elif wo.created_by_id:
                from app.models.user import User
                recipient_user = db.query(User).filter(User.id == wo.created_by_id).first()
                if recipient_user:
                    recipient_label = recipient_user.full_name or recipient_user.username or "מנהל עבודה"
            # Fallback: project manager
            if not recipient_user and wo.project and wo.project.manager_id:
                from app.models.user import User
                recipient_user = db.query(User).filter(User.id == wo.project.manager_id).first()
                if recipient_user:
                    recipient_label = recipient_user.full_name or "מנהל פרויקט"

            if recipient_user and recipient_user.email:
                from app.core.email import send_email
                supplier_name_str = ""
                if wo.supplier_id:
                    from app.models.supplier import Supplier
                    s = db.query(Supplier).filter(Supplier.id == wo.supplier_id).first()
                    if s:
                        supplier_name_str = s.name or ""

                subject = f"הזמנה {order_label} אושרה לביצוע"
                body = (
                    f"שלום {recipient_label},\n\n"
                    f"הזמנת העבודה מספר {order_label} אושרה על ידי מתאם ההזמנות ונשלחה לביצוע.\n"
                    f"{'ספק: ' + supplier_name_str + chr(10) if supplier_name_str else ''}"
                    f"{location_line}"
                    f"{waze_line}\n\n"
                    f"אושר על ידי: {admin_name}\n\n"
                    "Forewise"
                )
                send_email(to=recipient_user.email, subject=subject, body=body)
                log.info(f"Approval email sent to work manager {recipient_user.email} for WO {wo_id}")
        except Exception as e:
            log.warning(f"Failed to send work manager approval email for WO {wo_id}: {e}")

        # ── In-app notification ───────────────────────────────────────────
        try:
            from app.services.notification_service import notification_service
            from app.schemas.notification import NotificationCreate

            notif_user_ids = set()
            if uid:
                pass  # don't notify the approver themselves
            if wo.created_by_id:
                notif_user_ids.add(wo.created_by_id)
            if wo.project and wo.project.manager_id:
                notif_user_ids.add(wo.project.manager_id)

            for nuid in notif_user_ids:
                if nuid == uid:
                    continue  # skip the person who approved
                import json as _json
                notif = NotificationCreate(
                    user_id=nuid,
                    title=f"הזמנה {order_label} אושרה ✅",
                    message=f"הזמנת עבודה {order_label} אושרה לביצוע על ידי {admin_name}.",
                    notification_type="work_order_approved",
                    priority="high",
                    channel="in_app",
                    entity_type="work_order",
                    entity_id=wo_id,
                    data=_json.dumps({"work_order_id": wo_id, "approved_by": admin_name}),
                    action_url=f"/work-orders/{wo_id}",
                )
                notification_service.create_notification(db, notif)
        except Exception as e:
            log.warning(f"Failed to create approval notification for WO {wo_id}: {e}")

        return wo

    def reject(self, db, wo_id, request=None, reason=None, current_user=None, current_user_id=None):
        """Reject a work order → rejected."""
        from app.models.work_order import WorkOrder
        import datetime
        wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
        if wo:
            wo.status = 'REJECTED'
            wo.updated_at = datetime.datetime.now()
            db.commit()
            db.refresh(wo)
        return wo

    def cancel(self, db, wo_id, notes=None, version=None, current_user=None, current_user_id=None):
        """Cancel a work order → cancelled."""
        from app.models.work_order import WorkOrder
        import datetime
        wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
        if wo:
            wo.status = 'CANCELLED'
            wo.updated_at = datetime.datetime.now()
            db.commit()
            db.refresh(wo)
        return wo

    def start(self, db, wo_id, request=None, current_user=None, current_user_id=None):
        """Start a work order → active."""
        from app.models.work_order import WorkOrder
        import datetime
        wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
        if wo:
            wo.status = 'ACTIVE'
            wo.updated_at = datetime.datetime.now()
            db.commit()
            db.refresh(wo)
        return wo

    def close(self, db, wo_id, actual_hours=None, version=None, current_user=None, current_user_id=None):
        """Close/complete a work order → completed."""
        from app.models.work_order import WorkOrder
        import datetime
        wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
        if wo:
            wo.status = 'completed'
            wo.updated_at = datetime.datetime.now()
            db.commit()
            db.refresh(wo)
        return wo

    def move_to_next_supplier(self, db, wo_id, current_user=None, current_user_id=None):
        """Move to next supplier in rotation."""
        return self.handle_supplier_response(db, wo_id, accepted=False)

    def resend_to_supplier(self, db, wo_id, current_user=None, current_user_id=None):
        """Resend work order to supplier."""
        return self.get_work_order(db, wo_id)

