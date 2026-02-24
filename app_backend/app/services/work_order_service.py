"""
WorkOrder Service - לוגיקה עסקית להזמנות עבודה
Handles all business logic including state machine
"""

from datetime import datetime
from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, or_, func

from app.models.work_order import WorkOrder
from app.models.project import Project
from app.models.supplier import Supplier
from app.models.supplier_rotation import SupplierRotation
from app.models.supplier_equipment import SupplierEquipment
from app.models.equipment_model import EquipmentModel
from app.models.equipment import Equipment
from app.models.location import Location
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderSearch,
    WorkOrderStatusUpdate,
    WorkOrderApproveRequest,
    WorkOrderRejectRequest,
    WorkOrderStatistics,
    WorkOrderStatus
)
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException
from app.services import activity_logger


class WorkOrderService(BaseService[WorkOrder]):
    LEGACY_BLOCKED_MODEL_NAMES = {
        "LEGACY_UNKNOWN_DO_NOT_ROTATE",
        "ציוד לא מזוהה (דורש השלמה)",
    }

    """
    WorkOrder Service - שירות הזמנות עבודה
    
    Business rules:
    1. order_number must be unique
    2. FK validation: project_id (required), supplier_id, equipment_id, location_id
    3. Status state machine validation
    4. Equipment required when status = APPROVED or ACTIVE
    5. Cannot delete if status = ACTIVE or COMPLETED
    """
    
    def __init__(self):
        super().__init__(WorkOrder)

    def _is_legacy_blocked_model(self, model: EquipmentModel) -> bool:
        name = (model.name or "").strip()
        return name in self.LEGACY_BLOCKED_MODEL_NAMES

    def _get_matching_supplier_ids(self, db: Session, requested_equipment_model_id: Optional[int]) -> List[int]:
        """Return supplier IDs that have the requested equipment model and availability."""
        if not requested_equipment_model_id:
            raise ValidationException("requested_equipment_model_id is required for supplier selection")

        supplier_ids = (
            db.query(SupplierEquipment.supplier_id)
            .filter(
                SupplierEquipment.equipment_model_id == requested_equipment_model_id,
                SupplierEquipment.is_active == True,
                or_(SupplierEquipment.status.is_(None), func.lower(SupplierEquipment.status) == "available"),
                or_(SupplierEquipment.quantity_available.is_(None), SupplierEquipment.quantity_available > 0),
            )
            .distinct()
            .all()
        )
        result = [sid for (sid,) in supplier_ids]
        if not result:
            raise ValidationException("לא נמצאו ספקים עם דגם הכלי המבוקש")
        return result

    def supplier_has_required_tool(self, db: Session, supplier_id: int, requested_equipment_model_id: Optional[int]) -> bool:
        """Validate that a supplier has the exact requested equipment model."""
        if not requested_equipment_model_id:
            return False

        exists = (
            db.query(SupplierEquipment.id)
            .filter(
                SupplierEquipment.supplier_id == supplier_id,
                SupplierEquipment.equipment_model_id == requested_equipment_model_id,
                SupplierEquipment.is_active == True,
                or_(SupplierEquipment.status.is_(None), func.lower(SupplierEquipment.status) == "available"),
                or_(SupplierEquipment.quantity_available.is_(None), SupplierEquipment.quantity_available > 0),
            )
            .first()
        )
        return exists is not None

    def select_next_supplier(
        self,
        db: Session,
        work_order: WorkOrder,
        *,
        constraint_mode: bool = False,
        exclude_supplier_ids: Optional[List[int]] = None,
    ) -> tuple[int, Optional[SupplierRotation]]:
        """
        Single source of truth for supplier selection.
        - Always enforce tool match.
        - Normal mode: prioritize area/region + availability.
        - Constraint mode: nationwide (still tool match).
        """
        exclude_supplier_ids = exclude_supplier_ids or []
        requested_model = db.query(EquipmentModel).filter_by(id=work_order.requested_equipment_model_id).first()
        if requested_model and self._is_legacy_blocked_model(requested_model):
            raise ValidationException("הזמנה ישנה ללא דגם ציוד - נדרש עדכון ידני לפני רוטציה")

        matching_supplier_ids = self._get_matching_supplier_ids(db, work_order.requested_equipment_model_id)

        base_rotation_query = (
            db.query(SupplierRotation)
            .join(Supplier, Supplier.id == SupplierRotation.supplier_id)
            .filter(
                SupplierRotation.supplier_id.in_(matching_supplier_ids),
                SupplierRotation.is_active == True,
                SupplierRotation.is_available == True,
                Supplier.is_active == True,
                Supplier.deleted_at.is_(None),
                ~SupplierRotation.supplier_id.in_(exclude_supplier_ids) if exclude_supplier_ids else True,
            )
            .order_by(
                func.coalesce(SupplierRotation.total_assignments, 0).asc(),
                func.coalesce(SupplierRotation.rotation_position, 999999).asc(),
            )
        )

        if not constraint_mode and work_order.project_id:
            project = db.query(Project).filter(Project.id == work_order.project_id).first()
            if project and project.area_id:
                area_candidate = base_rotation_query.filter(SupplierRotation.area_id == project.area_id).first()
                if area_candidate:
                    return area_candidate.supplier_id, area_candidate
            if project and project.region_id:
                region_candidate = base_rotation_query.filter(SupplierRotation.region_id == project.region_id).first()
                if region_candidate:
                    return region_candidate.supplier_id, region_candidate

        global_candidate = base_rotation_query.first()
        if global_candidate:
            return global_candidate.supplier_id, global_candidate

        # Fallback: suppliers with the tool but without rotation row.
        fallback_supplier = (
            db.query(Supplier)
            .filter(
                Supplier.id.in_(matching_supplier_ids),
                Supplier.is_active == True,
                Supplier.deleted_at.is_(None),
                ~Supplier.id.in_(exclude_supplier_ids) if exclude_supplier_ids else True,
            )
            .order_by(Supplier.last_selected.asc().nullsfirst(), Supplier.id.asc())
            .first()
        )
        if fallback_supplier:
            return fallback_supplier.id, None

        raise ValidationException("No eligible suppliers found for selected tool")
    
    def _generate_order_number(self, db: Session) -> int:
        """
        Generate unique order number
        
        Args:
            db: Database session
        
        Returns:
            Next order number
        """
        max_number = db.query(func.max(WorkOrder.order_number)).scalar() or 0
        return max_number + 1
    
    def create(
        self,
        db: Session,
        data: WorkOrderCreate,
        current_user_id: int
    ) -> WorkOrder:
        """
        Create new work order
        
        Args:
            db: Database session
            data: Work order creation data
            current_user_id: User creating the work order
        
        Returns:
            Created work order
        
        Raises:
            ValidationException: If validation fails
            DuplicateException: If constraint violated
        """
        # Validate FK: project_id (REQUIRED!)
        project = db.query(Project).filter_by(id=data.project_id).first()
        if not project:
            raise ValidationException(f"Project {data.project_id} not found")
        if not project.is_active:
            raise ValidationException(f"Project {data.project_id} is not active")
        
        requested_equipment_model = db.query(EquipmentModel).filter_by(id=data.requested_equipment_model_id).first()
        if not requested_equipment_model or not requested_equipment_model.is_active:
            raise ValidationException(f"Equipment model {data.requested_equipment_model_id} not found or inactive")
        if self._is_legacy_blocked_model(requested_equipment_model):
            raise ValidationException("לא ניתן ליצור הזמנה חדשה עם ציוד לא מזוהה")

        # Validate FK: supplier_id (if provided)
        if data.supplier_id:
            supplier = db.query(Supplier).filter_by(id=data.supplier_id).first()
            if not supplier:
                raise ValidationException(f"Supplier {data.supplier_id} not found")
            if not supplier.is_active:
                raise ValidationException(f"Supplier {data.supplier_id} is not active")
            if not self.supplier_has_required_tool(db, data.supplier_id, data.requested_equipment_model_id):
                raise ValidationException("לא ניתן לבחור ספק שאין לו את דגם הכלי המבוקש")
            if data.is_forced_selection and not data.constraint_reason_id:
                raise ValidationException("בחירת ספק באילוץ מחייבת סיבת אילוץ")
            if data.is_forced_selection:
                notes = (data.constraint_notes or "").strip()
                if len(notes) < 10:
                    raise ValidationException("בחירת ספק באילוץ מחייבת נימוק טקסטואלי (לפחות 10 תווים)")
        
        # Validate FK: equipment_id (if provided)
        if data.equipment_id:
            equipment = db.query(Equipment).filter_by(id=data.equipment_id).first()
            if not equipment:
                raise ValidationException(f"Equipment {data.equipment_id} not found")
            if equipment.status not in ('available', 'in_use'):
                raise ValidationException(f"Equipment {data.equipment_id} is not available (status: {equipment.status})")
        
        # Validate FK: location_id (if provided)
        if data.location_id:
            location = db.query(Location).filter_by(id=data.location_id).first()
            if not location:
                raise ValidationException(f"Location {data.location_id} not found")
        
        # Business validation: dates
        if data.work_start_date and data.work_end_date:
            if data.work_end_date < data.work_start_date:
                raise ValidationException("work_end_date must be after work_start_date")
        
        # BUDGET VALIDATION (CRITICAL!)
        # Check if project has budget and if there's remaining balance
        if project.budget_id and project.budget:
            budget = project.budget
            remaining_budget = budget.remaining_amount  # Uses property: total - spent - committed
            estimated_cost = data.total_amount or (data.estimated_hours or Decimal(0)) * (data.hourly_rate or Decimal(0))
            
            if remaining_budget <= 0:
                raise ValidationException(
                    f"אין יתרה תקציבית לפרויקט {project.name}. "
                    f"תקציב: ₪{budget.total_amount:,.2f}, מנוצל: ₪{(budget.spent_amount or 0) + (budget.committed_amount or 0):,.2f}"
                )
            
            if estimated_cost > 0 and estimated_cost > remaining_budget:
                raise ValidationException(
                    f"עלות משוערת (₪{estimated_cost:,.2f}) חורגת מהיתרה התקציבית (₪{remaining_budget:,.2f}). "
                    f"נדרש אישור מנהל אזור/מרחב."
                )
        
        # Generate order_number
        order_number = self._generate_order_number(db)
        
        # Create work order
        work_order_dict = data.model_dump(exclude_unset=True)
        work_order_dict['order_number'] = order_number
        work_order_dict['created_by_id'] = current_user_id
        work_order_dict['charged_amount'] = Decimal(0)
        
        work_order = WorkOrder(**work_order_dict)
        
        db.add(work_order)
        db.commit()
        db.refresh(work_order)
        
        # Log activity
        activity_logger.log_work_order_created(
            db=db,
            work_order_id=work_order.id,
            user_id=current_user_id,
            project_id=data.project_id,
            details={"order_number": order_number, "title": data.title}
        )
        
        return work_order
    
    def update(
        self,
        db: Session,
        work_order_id: int,
        data: WorkOrderUpdate,
        current_user_id: int
    ) -> WorkOrder:
        """
        Update work order
        
        Args:
            db: Database session
            work_order_id: Work order ID
            data: Update data
            current_user_id: User updating
        
        Returns:
            Updated work order
        
        Raises:
            NotFoundException: If work order not found
            ValidationException: If validation fails
            DuplicateException: If version mismatch
        """
        work_order = self.get_by_id_or_404(db, work_order_id, include_deleted=False)
        
        # Version check (optimistic locking)
        if data.version is not None and work_order.version != data.version:
            raise DuplicateException(
                f"Work order was modified by another user. "
                f"Expected version {data.version}, current is {work_order.version}"
            )
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        # Validate FKs if changed
        if 'project_id' in update_dict and update_dict['project_id']:
            project = db.query(Project).filter_by(id=update_dict['project_id']).first()
            if not project:
                raise ValidationException(f"Project {update_dict['project_id']} not found")
        
        if 'supplier_id' in update_dict and update_dict['supplier_id']:
            supplier = db.query(Supplier).filter_by(id=update_dict['supplier_id']).first()
            if not supplier:
                raise ValidationException(f"Supplier {update_dict['supplier_id']} not found")
        
        if 'equipment_id' in update_dict and update_dict['equipment_id']:
            equipment = db.query(Equipment).filter_by(id=update_dict['equipment_id']).first()
            if not equipment:
                raise ValidationException(f"Equipment {update_dict['equipment_id']} not found")

        if 'requested_equipment_model_id' in update_dict and update_dict['requested_equipment_model_id']:
            req_model = db.query(EquipmentModel).filter_by(id=update_dict['requested_equipment_model_id']).first()
            if not req_model or not req_model.is_active:
                raise ValidationException(f"Equipment model {update_dict['requested_equipment_model_id']} not found or inactive")
            if self._is_legacy_blocked_model(req_model):
                raise ValidationException("לא ניתן לעדכן הזמנה למודל Legacy לא מזוהה")
        
        # Update fields
        for field, value in update_dict.items():
            setattr(work_order, field, value)
        
        # Increment version
        if work_order.version is not None:
            work_order.version += 1
        
        db.commit()
        db.refresh(work_order)
        
        return work_order
    
    def list(
        self,
        db: Session,
        search: WorkOrderSearch
    ) -> Tuple[List[WorkOrder], int]:
        """
        List work orders with filters - optimized with eager loading
        
        Args:
            db: Database session
            search: Search filters
        
        Returns:
            Tuple of (work orders list, total count)
        """
        # Use eager loading to prevent N+1 queries
        query = self._base_query(db, include_deleted=search.include_deleted).options(
            joinedload(WorkOrder.project),
            joinedload(WorkOrder.supplier),
            joinedload(WorkOrder.equipment),
            joinedload(WorkOrder.location),
            joinedload(WorkOrder.created_by)
        )
        
        # Build filter conditions for reuse in count query
        filter_conditions = []
        
        # Free text search
        if search.q:
            search_term = f"%{search.q}%"
            filter_conditions.append(
                or_(
                    WorkOrder.title.ilike(search_term),
                    WorkOrder.description.ilike(search_term),
                    WorkOrder.order_number == int(search.q) if search.q.isdigit() else False
                )
            )
        
        # Filters
        if search.project_id:
            filter_conditions.append(WorkOrder.project_id == search.project_id)

        if search.area_id is not None:
            area_project_ids = select(Project.id).where(Project.area_id == search.area_id)
            filter_conditions.append(WorkOrder.project_id.in_(area_project_ids))
        
        if search.supplier_id:
            filter_conditions.append(WorkOrder.supplier_id == search.supplier_id)
        
        if search.equipment_id:
            filter_conditions.append(WorkOrder.equipment_id == search.equipment_id)

        if search.requested_equipment_model_id:
            filter_conditions.append(WorkOrder.requested_equipment_model_id == search.requested_equipment_model_id)
        
        if search.location_id:
            filter_conditions.append(WorkOrder.location_id == search.location_id)
        
        if search.status:
            filter_conditions.append(WorkOrder.status == search.status.value)
        
        if search.priority:
            filter_conditions.append(WorkOrder.priority == search.priority.value)
        
        if search.created_by_id:
            filter_conditions.append(WorkOrder.created_by_id == search.created_by_id)
        
        if search.is_active is not None:
            filter_conditions.append(WorkOrder.is_active == search.is_active)
        
        # Date range
        if search.start_date_from:
            filter_conditions.append(WorkOrder.work_start_date >= search.start_date_from)
        
        if search.start_date_to:
            filter_conditions.append(WorkOrder.work_start_date <= search.start_date_to)
        
        # Apply filters to query
        for condition in filter_conditions:
            query = query.where(condition)
        
        # Count query - simple, no eager loading
        count_query = select(func.count(WorkOrder.id))
        if not search.include_deleted and self._has_deleted_at:
            count_query = count_query.where(WorkOrder.deleted_at.is_(None))
        for condition in filter_conditions:
            count_query = count_query.where(condition)
        
        total = db.execute(count_query).scalar() or 0
        
        # Sort
        sort_column = getattr(WorkOrder, search.sort_by, WorkOrder.created_at)
        if search.sort_desc:
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Paginate
        offset = (search.page - 1) * search.page_size
        query = query.offset(offset).limit(search.page_size)
        
        work_orders = db.execute(query).scalars().unique().all()
        
        return work_orders, total
    
    def soft_delete(
        self,
        db: Session,
        work_order_id: int,
        current_user_id: int
    ) -> WorkOrder:
        """
        Soft delete work order
        
        Args:
            db: Database session
            work_order_id: Work order ID
            current_user_id: User deleting
        
        Returns:
            Soft-deleted work order
        
        Raises:
            ValidationException: If cannot delete (active or completed)
        """
        work_order = self.get_by_id_or_404(db, work_order_id)
        
        # Business rule: Cannot delete if ACTIVE or COMPLETED
        if work_order.status in ('ACTIVE', 'COMPLETED'):
            raise ValidationException(
                f"Cannot delete work order with status '{work_order.status}'. "
                "Cancel or close it first."
            )
        
        # Soft delete
        deleted = super().soft_delete(db, work_order_id, commit=True)
        
        return deleted
    
    def approve(
        self,
        db: Session,
        work_order_id: int,
        request: WorkOrderApproveRequest,
        current_user_id: int
    ) -> WorkOrder:
        """
        Approve work order
        
        Business Rule: equipment_id is REQUIRED when approving!
        
        Args:
            db: Database session
            work_order_id: Work order ID
            request: Approve request data
            current_user_id: User approving
        
        Returns:
            Approved work order
        
        Raises:
            ValidationException: If validation fails
        """
        work_order = self.get_by_id_or_404(db, work_order_id)
        
        # Version check
        if request.version is not None and work_order.version != request.version:
            raise DuplicateException("Work order was modified by another user")
        
        # Business rule: Must be PENDING to approve
        if work_order.status != 'PENDING':
            raise ValidationException(f"Can only approve PENDING work orders (current: {work_order.status})")
        
        # Business rule: equipment_id required for approval
        equipment_id = request.equipment_id or work_order.equipment_id
        if not equipment_id:
            raise ValidationException("equipment_id is required when approving work order")
        
        # Validate equipment
        equipment = db.query(Equipment).filter_by(id=equipment_id).first()
        if not equipment:
            raise ValidationException(f"Equipment {equipment_id} not found")
        
        # Update work order
        work_order.status = 'APPROVED'
        work_order.equipment_id = equipment_id
        
        if request.supplier_id:
            work_order.supplier_id = request.supplier_id
        
        if request.hourly_rate:
            work_order.hourly_rate = request.hourly_rate
        
        if work_order.version is not None:
            work_order.version += 1
        
        db.commit()
        db.refresh(work_order)
        
        # Log activity
        activity_logger.log_work_order_approved(
            db=db,
            work_order_id=work_order.id,
            user_id=current_user_id,
            equipment_id=equipment_id
        )
        
        return work_order
    
    def reject(
        self,
        db: Session,
        work_order_id: int,
        request: WorkOrderRejectRequest,
        current_user_id: int
    ) -> WorkOrder:
        """
        Reject work order
        
        Args:
            db: Database session
            work_order_id: Work order ID
            request: Reject request (must include rejection_reason_id)
            current_user_id: User rejecting
        
        Returns:
            Rejected work order
        """
        work_order = self.get_by_id_or_404(db, work_order_id)
        
        # Version check
        if request.version is not None and work_order.version != request.version:
            raise DuplicateException("Work order was modified by another user")
        
        # Business rule: Can only reject PENDING
        if work_order.status != 'PENDING':
            raise ValidationException(f"Can only reject PENDING work orders (current: {work_order.status})")
        
        # Update
        work_order.status = 'REJECTED'
        work_order.rejection_reason_id = request.rejection_reason_id
        work_order.rejection_notes = request.rejection_notes
        
        if work_order.version is not None:
            work_order.version += 1
        
        db.commit()
        db.refresh(work_order)
        
        # Log activity
        activity_logger.log_work_order_rejected(
            db=db,
            work_order_id=work_order.id,
            user_id=current_user_id,
            reason=request.rejection_notes
        )
        
        return work_order
    
    def cancel(
        self,
        db: Session,
        work_order_id: int,
        notes: Optional[str],
        version: Optional[int],
        current_user_id: int
    ) -> WorkOrder:
        """
        Cancel work order
        
        Args:
            db: Database session
            work_order_id: Work order ID
            notes: Cancellation notes
            version: Version for optimistic locking
            current_user_id: User cancelling
        
        Returns:
            Cancelled work order
        """
        work_order = self.get_by_id_or_404(db, work_order_id)
        
        # Version check
        if version is not None and work_order.version != version:
            raise DuplicateException("Work order was modified by another user")
        
        # Business rule: Cannot cancel COMPLETED
        if work_order.status == 'COMPLETED':
            raise ValidationException("Cannot cancel COMPLETED work order")
        
        work_order.status = 'CANCELLED'
        
        if work_order.version is not None:
            work_order.version += 1
        
        db.commit()
        db.refresh(work_order)
        
        # Log activity
        activity_logger.log_work_order_cancelled(
            db=db,
            work_order_id=work_order.id,
            user_id=current_user_id,
            reason=notes
        )
        
        return work_order
    
    def close(
        self,
        db: Session,
        work_order_id: int,
        actual_hours: Optional[Decimal],
        version: Optional[int],
        current_user_id: int
    ) -> WorkOrder:
        """
        Close/Complete work order
        
        Args:
            db: Database session
            work_order_id: Work order ID
            actual_hours: Actual hours worked
            version: Version for optimistic locking
            current_user_id: User closing
        
        Returns:
            Completed work order
        """
        work_order = self.get_by_id_or_404(db, work_order_id)
        
        # Version check
        if version is not None and work_order.version != version:
            raise DuplicateException("Work order was modified by another user")
        
        # Business rule: Must be ACTIVE to complete
        if work_order.status != 'ACTIVE':
            raise ValidationException(f"Can only complete ACTIVE work orders (current: {work_order.status})")
        
        work_order.status = 'COMPLETED'
        
        if actual_hours:
            work_order.actual_hours = actual_hours
        
        if work_order.version is not None:
            work_order.version += 1
        
        db.commit()
        db.refresh(work_order)
        
        # Log activity
        activity_logger.log_work_order_closed(
            db=db,
            work_order_id=work_order.id,
            user_id=current_user_id,
            actual_hours=float(actual_hours) if actual_hours else None
        )
        
        return work_order
    
    def get_statistics(
        self,
        db: Session,
        filters: Optional[dict] = None
    ) -> WorkOrderStatistics:
        """
        Get work order statistics
        
        Args:
            db: Database session
            filters: Optional filters (project_id, supplier_id, etc.)
        
        Returns:
            Work order statistics
        """
        query = select(WorkOrder).where(WorkOrder.deleted_at.is_(None))
        
        # Apply filters
        if filters:
            if filters.get('project_id'):
                query = query.where(WorkOrder.project_id == filters['project_id'])
            if filters.get('supplier_id'):
                query = query.where(WorkOrder.supplier_id == filters['supplier_id'])
        
        # Get all work orders
        all_work_orders = db.execute(query).scalars().all()
        
        # Calculate statistics
        stats = WorkOrderStatistics(
            total=len(all_work_orders),
            pending_count=sum(1 for wo in all_work_orders if wo.status == 'PENDING'),
            approved_count=sum(1 for wo in all_work_orders if wo.status == 'APPROVED'),
            active_count=sum(1 for wo in all_work_orders if wo.status == 'ACTIVE'),
            completed_count=sum(1 for wo in all_work_orders if wo.status == 'COMPLETED'),
            total_frozen_amount=sum(wo.frozen_amount or 0 for wo in all_work_orders),
            total_charged_amount=sum(wo.charged_amount or 0 for wo in all_work_orders)
        )
        
        # By status
        by_status = {}
        for wo in all_work_orders:
            if wo.status:
                by_status[wo.status] = by_status.get(wo.status, 0) + 1
        stats.by_status = by_status
        
        # By priority
        by_priority = {}
        for wo in all_work_orders:
            if wo.priority:
                by_priority[wo.priority] = by_priority.get(wo.priority, 0) + 1
        stats.by_priority = by_priority
        
        return stats
    
    def start(
        self,
        db: Session,
        work_order_id: int,
        current_user_id: int
    ) -> WorkOrder:
        """
        Start work order (transition to IN_PROGRESS)
        
        Args:
            db: Database session
            work_order_id: Work order ID
            current_user_id: User starting
        
        Returns:
            Started work order
        """
        work_order = self.get_by_id_or_404(db, work_order_id)
        
        # Business rule: Must be APPROVED to start
        if work_order.status not in ('APPROVED', 'ACTIVE'):
            raise ValidationException(f"Can only start APPROVED work orders (current: {work_order.status})")
        
        work_order.status = 'ACTIVE'
        
        if work_order.version is not None:
            work_order.version += 1
        
        db.commit()
        db.refresh(work_order)
        
        # Log activity
        activity_logger.log_work_order_started(
            db=db,
            work_order_id=work_order.id,
            user_id=current_user_id
        )
        
        return work_order
    
    def update_status(
        self,
        db: Session,
        work_order_id: int,
        status_update: WorkOrderStatusUpdate,
        current_user_id: int
    ) -> WorkOrder:
        """
        Update work order status (generic)
        
        Args:
            db: Database session
            work_order_id: Work order ID
            status_update: Status update data
            current_user_id: User updating
        
        Returns:
            Updated work order
        """
        work_order = self.get_by_id_or_404(db, work_order_id)
        
        # Check if transitioning to in_progress/active
        if status_update.status and status_update.status.lower() in ('in_progress', 'active'):
            return self.start(db, work_order_id, current_user_id)
        
        # Generic status update
        if status_update.status:
            work_order.status = status_update.status.upper()
        
        if work_order.version is not None:
            work_order.version += 1
        
        db.commit()
        db.refresh(work_order)
        
        return work_order
    
    def get_by_order_number(
        self,
        db: Session,
        order_number: int,
        include_deleted: bool = False
    ) -> Optional[WorkOrder]:
        """
        Get work order by order number
        
        Args:
            db: Database session
            order_number: Order number
            include_deleted: Include soft-deleted
        
        Returns:
            Work order or None
        """
        query = select(WorkOrder).where(WorkOrder.order_number == order_number)
        
        if not include_deleted:
            query = query.where(WorkOrder.deleted_at.is_(None))
        
        return db.execute(query).scalar_one_or_none()
    
    # ============================================
    # COORDINATION METHODS
    # For Order Coordinator role
    # ============================================
    
    def send_to_supplier(
        self,
        db: Session,
        work_order_id: int,
        current_user_id: int
    ) -> WorkOrder:
        """
        Send work order to supplier via portal
        Generates portal token with 3-hour expiry
        
        Args:
            db: Database session
            work_order_id: Work order ID
            current_user_id: User sending
        
        Returns:
            Updated work order with portal token
        """
        import secrets
        from datetime import timedelta
        
        work_order = self.get_by_id_or_404(db, work_order_id)
        
        # Business rule: Must have a supplier
        if not work_order.supplier_id:
            raise ValidationException("Work order must have a supplier assigned")
        
        # Generate portal token (3 hours expiry)
        work_order.portal_token = secrets.token_urlsafe(32)
        work_order.portal_expiry = datetime.utcnow() + timedelta(hours=3)
        work_order.token_expires_at = work_order.portal_expiry
        
        if work_order.version is not None:
            work_order.version += 1
        
        db.commit()
        db.refresh(work_order)
        
        # Log activity
        activity_logger.log_work_order_sent_to_supplier(
            db=db,
            work_order_id=work_order.id,
            user_id=current_user_id,
            supplier_id=work_order.supplier_id
        )
        
        return work_order
    
    def move_to_next_supplier(
        self,
        db: Session,
        work_order_id: int,
        current_user_id: int
    ) -> WorkOrder:
        """
        Move work order to next supplier in fair rotation
        
        Args:
            db: Database session
            work_order_id: Work order ID
            current_user_id: User moving
        
        Returns:
            Updated work order with new supplier
        """
        work_order = self.get_by_id_or_404(db, work_order_id)
        old_supplier_id = work_order.supplier_id

        next_supplier_id, rotation_row = self.select_next_supplier(
            db,
            work_order,
            constraint_mode=bool(work_order.is_forced_selection),
            exclude_supplier_ids=[old_supplier_id] if old_supplier_id else None,
        )

        work_order.supplier_id = next_supplier_id
        work_order.portal_token = None  # Clear old token
        work_order.portal_expiry = None
        work_order.token_expires_at = None

        if rotation_row:
            rotation_row.total_assignments = (rotation_row.total_assignments or 0) + 1
            rotation_row.last_assignment_date = datetime.utcnow().date()
        
        if work_order.version is not None:
            work_order.version += 1
        
        db.commit()
        db.refresh(work_order)
        
        # Log activity
        activity_logger.log_work_order_supplier_changed(
            db=db,
            work_order_id=work_order.id,
            user_id=current_user_id,
            old_supplier_id=old_supplier_id,
            new_supplier_id=next_supplier_id
        )
        
        return work_order
    
    def resend_to_supplier(
        self,
        db: Session,
        work_order_id: int,
        current_user_id: int
    ) -> WorkOrder:
        """
        Resend work order to current supplier (extend portal token)
        
        Args:
            db: Database session
            work_order_id: Work order ID
            current_user_id: User resending
        
        Returns:
            Updated work order with new token expiry
        """
        import secrets
        from datetime import timedelta
        
        work_order = self.get_by_id_or_404(db, work_order_id)
        
        # Business rule: Must have a supplier
        if not work_order.supplier_id:
            raise ValidationException("Work order must have a supplier assigned")
        
        # Generate new portal token with 3-hour expiry
        work_order.portal_token = secrets.token_urlsafe(32)
        work_order.portal_expiry = datetime.utcnow() + timedelta(hours=3)
        work_order.token_expires_at = work_order.portal_expiry
        
        if work_order.version is not None:
            work_order.version += 1
        
        db.commit()
        db.refresh(work_order)
        
        # Log activity
        activity_logger.log_work_order_resent_to_supplier(
            db=db,
            work_order_id=work_order.id,
            user_id=current_user_id,
            supplier_id=work_order.supplier_id
        )
        
        return work_order
