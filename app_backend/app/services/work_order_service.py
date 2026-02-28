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
        """Get list of work orders with filters."""
        query = db.query(WorkOrder)

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
        wo_dict.setdefault("status", "PENDING")

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
        """Soft delete work order."""
        db_work_order = self.get_work_order(db, work_order_id)
        if not db_work_order:
            return False

        db_work_order.is_active = False
        db_work_order.updated_at = datetime.utcnow()
        db.commit()
        return True

    def send_to_supplier(self, db: Session, work_order_id: int, current_user_id: int = None) -> dict:
        """
        Send work order to supplier — generates portal token and sends email.
        Returns dict with { work_order, portal_token, portal_url, expires_at }.
        """
        import secrets
        from datetime import timedelta
        from app.core.config import settings

        work_order = self.get_work_order(db, work_order_id)
        if not work_order:
            from app.core.exceptions import NotFoundException
            raise NotFoundException(f"Work order {work_order_id} not found")

        # Accept PENDING, DISTRIBUTING, or pending statuses
        allowed = {'pending', 'PENDING', 'DISTRIBUTING', 'distributing', 'draft', 'DRAFT'}
        if work_order.status not in allowed:
            from app.core.exceptions import ValidationException
            raise ValidationException(
                f"Work order must be in PENDING status to send to supplier (current: {work_order.status})"
            )

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

        # Send email to supplier (best-effort)
        if work_order.supplier_id:
            try:
                from app.models.supplier import Supplier
                supplier = db.query(Supplier).filter(Supplier.id == work_order.supplier_id).first()
                if supplier and (supplier.email or supplier.contact_email):
                    from app.core.email import send_email
                    to_email = supplier.email or supplier.contact_email
                    send_email(
                        to=to_email,
                        subject=f"הזמנת עבודה מספר {work_order.order_number} - דורש תגובה",
                        body=(
                            f"שלום {supplier.name},\n\n"
                            f"קיבלת הזמנת עבודה חדשה מקק\"ל.\n"
                            f"הזמנה: {work_order.title or work_order.order_number}\n\n"
                            f"לצפייה ואישור/דחייה:\n{portal_url}\n\n"
                            f"הקישור תקף עד: {expires_at.strftime('%d/%m/%Y %H:%M')}\n\n"
                            "קק\"ל"
                        ),
                    )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to send portal email: {e}")

        return {
            "work_order": work_order,
            "portal_token": token,
            "portal_url": portal_url,
            "expires_at": expires_at.isoformat(),
        }

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
        """Alias → get_work_orders() returning (items, total) tuple"""
        items = self.get_work_orders(db)
        return items, len(items)

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
        """Approve a work order — DISTRIBUTING → approved."""
        from app.models.work_order import WorkOrder
        import datetime
        wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
        if wo:
            wo.status = 'approved'
            wo.updated_at = datetime.datetime.now()
            db.commit()
            db.refresh(wo)
        return wo

    def reject(self, db, wo_id, request=None, reason=None, current_user=None, current_user_id=None):
        """Reject a work order → rejected."""
        from app.models.work_order import WorkOrder
        import datetime
        wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
        if wo:
            wo.status = 'rejected'
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
            wo.status = 'cancelled'
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
            wo.status = 'active'
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

