# app/routers/supplier_portal.py
"""
Supplier Portal API endpoints - דף נחיתה לספקים
Public endpoints - no authentication required (token-based access)
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field

from app.core.database import get_db

logger = logging.getLogger(__name__)
from app.models.work_order import WorkOrder
from app.models.supplier import Supplier
from app.models.supplier_equipment import SupplierEquipment
from app.models.equipment_model import EquipmentModel
from app.models.project import Project
from app.models.equipment import Equipment

router = APIRouter(prefix="/supplier-portal", tags=["Supplier Portal"])


# ============================================
# SCHEMAS - Public Portal
# ============================================

class SupplierPortalResponse(BaseModel):
    """תגובה לדף נחיתה של ספק"""
    
    # Work Order Info
    order_number: int = Field(..., description="מספר הזמנה")
    title: Optional[str] = Field(None, description="כותרת ההזמנה")
    description: Optional[str] = Field(None, description="תיאור ההזמנה")
    status: Optional[str] = Field(None, description="סטטוס")
    priority: Optional[str] = Field(None, description="עדיפות")
    
    # Dates
    work_start_date: Optional[str] = Field(None, description="תאריך התחלה")
    work_end_date: Optional[str] = Field(None, description="תאריך סיום")
    
    # Equipment
    equipment_type: Optional[str] = Field(None, description="סוג ציוד")
    
    # Hours & Rates
    estimated_hours: Optional[float] = Field(None, description="שעות משוערות")
    hourly_rate: Optional[float] = Field(None, description="תעריף לשעה")
    total_amount: Optional[float] = Field(None, description="סכום כולל משוער")
    
    # Project Info
    project_name: Optional[str] = Field(None, description="שם פרויקט")
    region_name: Optional[str] = Field(None, description="מרחב")
    area_name: Optional[str] = Field(None, description="אזור")
    
    # Supplier Info
    supplier_name: Optional[str] = Field(None, description="שם הספק")
    supplier_id: Optional[int] = Field(None, description="מזהה ספק")
    
    # Token Info
    portal_token: str = Field(..., description="מזהה דף נחיתה")
    expires_at: Optional[datetime] = Field(None, description="תאריך פג תוקף")
    time_remaining_seconds: Optional[int] = Field(None, description="שניות נותרות")
    
    # Flags
    is_forced_selection: bool = Field(False, description="האם בחירת ספק כפויה")
    is_expired: bool = Field(False, description="האם פג תוקף")
    already_responded: bool = Field(False, description="האם כבר נענה")
    
    class Config:
        from_attributes = True


class SupplierAcceptRequest(BaseModel):
    """בקשת אישור הזמנה על ידי ספק"""
    equipment_id: Optional[int] = Field(None, description="supplier_equipment.id or equipment.id")
    supplier_equipment_id: Optional[int] = Field(None, description="supplier_equipment.id (explicit)")
    license_plate: Optional[str] = Field(None, description="מספר רישוי הכלי", max_length=20)
    notes: Optional[str] = Field(None, description="הערות הספק", max_length=500)


class SupplierRejectRequest(BaseModel):
    """בקשת דחיית הזמנה על ידי ספק"""
    reason_id: Optional[int] = Field(None, description="מזהה סיבת דחייה")
    notes: Optional[str] = Field(None, description="הערות", max_length=500)


class SupplierResponseResult(BaseModel):
    """תוצאת תגובת ספק"""
    success: bool
    message: str
    order_number: int


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_work_order_by_token(db: Session, portal_token: str) -> Optional[WorkOrder]:
    """Get work order by portal token with eager loading"""
    return (
        db.query(WorkOrder)
        .options(
            joinedload(WorkOrder.project).joinedload(Project.region),
            joinedload(WorkOrder.project).joinedload(Project.area),
            joinedload(WorkOrder.supplier),
            joinedload(WorkOrder.equipment)
        )
        .filter(WorkOrder.portal_token == portal_token)
        .first()
    )


def _get_blocking_work_order(db: Session, equipment_id: int, current_work_order_id: int) -> Optional[WorkOrder]:
    """Return another active work order already holding this equipment."""
    return (
        db.query(WorkOrder)
        .filter(
            WorkOrder.id != current_work_order_id,
            WorkOrder.equipment_id == equipment_id,
            WorkOrder.deleted_at.is_(None),
            WorkOrder.is_active == True,
            WorkOrder.status.isnot(None),
            WorkOrder.status.notin_([
                "COMPLETED",
                "CANCELLED",
                "REJECTED",
                "STOPPED",
                "EXPIRED",
            ]),
        )
        .first()
    )


def check_token_valid(work_order: WorkOrder) -> tuple[bool, str]:
    """Check if portal token is still valid"""
    now = datetime.utcnow()
    
    # Check expiry - try all expiry columns
    expiry = work_order.portal_expiry or work_order.token_expires_at or work_order.portal_token_expires
    
    if expiry and expiry < now:
        return False, "פג תוקף הקישור. אנא פנה למנהל העבודה לקבלת קישור חדש."
    
    # Check if already responded
    if work_order.response_received_at or work_order.supplier_response_at:
        return False, "כבר נענית להזמנה זו."
    
    # Check status - should be in a state waiting for supplier
    valid_statuses = ['PENDING', 'APPROVED', 'sent_to_supplier', 'DISTRIBUTING']
    if work_order.status and work_order.status not in valid_statuses:
        return False, f"ההזמנה כבר בסטטוס: {work_order.status}"
    
    return True, ""


# ============================================
# PUBLIC ENDPOINTS (No Auth Required)
# ============================================

@router.get("/{portal_token}", response_model=SupplierPortalResponse)
def get_supplier_portal_view(
    portal_token: str,
    db: Session = Depends(get_db)
):
    """
    קבלת פרטי הזמנה לדף נחיתה של ספק
    Public endpoint - no authentication required
    """
    # Find work order by token
    work_order = get_work_order_by_token(db, portal_token)
    
    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="הזמנה לא נמצאה. אנא ודא שהקישור תקין."
        )
    
    # Check token validity
    is_valid, error_message = check_token_valid(work_order)
    
    # Calculate time remaining
    now = datetime.utcnow()
    expiry = work_order.portal_expiry or work_order.token_expires_at or work_order.portal_token_expires
    time_remaining = None
    is_expired = False
    
    if expiry:
        if expiry > now:
            time_remaining = int((expiry - now).total_seconds())
        else:
            is_expired = True
    
    # Build response
    response = SupplierPortalResponse(
        # Work Order Info
        order_number=work_order.order_number,
        title=work_order.title,
        description=work_order.description,
        status=work_order.status,
        priority=work_order.priority,
        
        # Dates
        work_start_date=work_order.work_start_date.isoformat() if work_order.work_start_date else None,
        work_end_date=work_order.work_end_date.isoformat() if work_order.work_end_date else None,
        
        # Equipment
        equipment_type=work_order.equipment_type,
        
        # Hours & Rates
        estimated_hours=float(work_order.estimated_hours) if work_order.estimated_hours else None,
        hourly_rate=float(work_order.hourly_rate) if work_order.hourly_rate else None,
        total_amount=float(work_order.total_amount) if work_order.total_amount else None,
        
        # Project Info
        project_name=work_order.project.name if work_order.project else None,
        region_name=work_order.project.region.name if work_order.project and work_order.project.region else None,
        area_name=work_order.project.area.name if work_order.project and work_order.project.area else None,
        
        # Supplier Info
        supplier_name=work_order.supplier.name if work_order.supplier else None,
        supplier_id=work_order.supplier_id,
        
        # Token Info
        portal_token=portal_token,
        expires_at=expiry,
        time_remaining_seconds=time_remaining,
        
        # Flags
        is_forced_selection=work_order.is_forced_selection or False,
        is_expired=is_expired,
        already_responded=bool(work_order.response_received_at or work_order.supplier_response_at)
    )
    
    return response


@router.get("/{portal_token}/available-equipment")
def get_available_equipment(
    portal_token: str,
    db: Session = Depends(get_db)
):
    """
    מחזיר רשימת ציוד זמין לספק שתואם לסוג הכלי שהוזמן.
    תנאים:
1. equipment_model_id category_id = work_order.requested_equipment_model.category_id
    2. supplier_id = work_order.supplier_id
    3. status = 'available' (לא משויך להזמנה פעילה אחרת)
    """
    work_order = get_work_order_by_token(db, portal_token)
    if not work_order:
        raise HTTPException(status_code=404, detail="הזמנה לא נמצאה")

    is_valid, err = check_token_valid(work_order)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err)

    # Determine the required category_id from the requested model
    required_category_id = None
    requested_model = None
    if work_order.requested_equipment_model_id:
        requested_model = db.query(EquipmentModel).filter(
            EquipmentModel.id == work_order.requested_equipment_model_id
        ).first()
        if requested_model:
            required_category_id = requested_model.category_id

    supplier_id = work_order.supplier_id

    # Equipment rows for this supplier; blocking = another active WO holds this equipment_id
    from sqlalchemy import text as sa_text

    eq_rows = db.execute(
        sa_text(
            """
        SELECT e.id, e.name, e.license_plate, e.equipment_type, e.type_id,
               e.hourly_rate, e.status, e.is_active,
               blk.project_name AS blocked_project_name
        FROM equipment e
        LEFT JOIN (
            SELECT wo.equipment_id, p.name AS project_name
            FROM work_orders wo
            INNER JOIN projects p ON p.id = wo.project_id
            INNER JOIN (
                SELECT equipment_id, MIN(id) AS mid
                FROM work_orders
                WHERE id != :wo_id
                  AND equipment_id IS NOT NULL
                  AND deleted_at IS NULL
                  AND is_active = true
                  AND UPPER(COALESCE(status,'')) NOT IN (
                    'COMPLETED','CANCELLED','REJECTED','STOPPED','EXPIRED'
                  )
                GROUP BY equipment_id
            ) pick ON pick.mid = wo.id AND wo.equipment_id = pick.equipment_id
        ) blk ON blk.equipment_id = e.id
        WHERE e.supplier_id = :sid
            AND e.is_active = true
            AND e.license_plate IS NOT NULL AND e.license_plate != ''
            AND (:cid IS NULL OR e.category_id = :cid)
        ORDER BY e.license_plate
        """
        ),
        {
            "sid": supplier_id,
            "cid": required_category_id,
            "wo_id": work_order.id,
        },
    ).fetchall()

    equipment_list = []
    for row in eq_rows:
        blocked_name = row[8]
        is_blocked = blocked_name is not None
        equipment_list.append(
            {
                "id": row[0],
                "name": row[1],
                "license_plate": row[2],
                "equipment_type": row[3],
                "type_id": row[4],
                "hourly_rate": float(row[5]) if row[5] is not None else None,
                "is_available": not is_blocked,
                "is_blocked": is_blocked,
                "blocked_by": blocked_name if is_blocked else None,
            }
        )

    return {
        "required_category_id": required_category_id,
        "supplier_id": supplier_id,
        "equipment": equipment_list,
    }


@router.post("/{portal_token}/accept", response_model=SupplierResponseResult)
def accept_work_order(
    portal_token: str,
    request: SupplierAcceptRequest,
    db: Session = Depends(get_db)
):
    """
    אישור הזמנת עבודה על ידי ספק
    Public endpoint - token-based access
    """
    # Find work order
    work_order = get_work_order_by_token(db, portal_token)
    
    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="הזמנה לא נמצאה"
        )
    
    # Check token validity
    is_valid, error_message = check_token_valid(work_order)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    try:
        requested_model = None
        required_category_id = None
        if work_order.requested_equipment_model_id:
            requested_model = db.query(EquipmentModel).filter(
                EquipmentModel.id == work_order.requested_equipment_model_id
            ).first()
            if requested_model:
                required_category_id = requested_model.category_id

        # ── Resolve equipment from request ──────────────────────────
        se_id = request.supplier_equipment_id or request.equipment_id
        effective_plate = (request.license_plate or "").strip() or None
        resolved_equipment_id = None

        if se_id:
            # Step 1: try as Equipment.id first
            direct_eq = db.query(Equipment).filter(Equipment.id == se_id).first()
            if direct_eq and direct_eq.supplier_id == work_order.supplier_id:
                if required_category_id is not None and direct_eq.category_id != required_category_id:
                    raise HTTPException(status_code=400, detail="הכלי שנבחר אינו תואם לסוג שהוזמן")
                blocking_wo = _get_blocking_work_order(db, direct_eq.id, work_order.id)
                if blocking_wo:
                    raise HTTPException(
                        status_code=400,
                        detail=f"הכלי שנבחר כבר משויך להזמנה פעילה אחרת (#{blocking_wo.order_number or blocking_wo.id})",
                    )
                resolved_equipment_id = direct_eq.id
                effective_plate = effective_plate or direct_eq.license_plate
            else:
                # Step 2: treat as SupplierEquipment.id
                se = db.query(SupplierEquipment).filter(SupplierEquipment.id == se_id).first()
                if se:
                    if se.supplier_id != work_order.supplier_id:
                        raise HTTPException(status_code=400, detail="הכלי שנבחר אינו שייך לספק הנוכחי")
                    effective_plate = effective_plate or se.license_plate
                    se.status = 'busy'
                elif not direct_eq:
                    raise HTTPException(status_code=400, detail="הכלי שנבחר אינו קיים במערכת")

        # Step 3: resolve equipment_id from license plate
        if effective_plate and not resolved_equipment_id:
            matched = db.query(Equipment).filter(
                Equipment.license_plate == effective_plate,
                Equipment.supplier_id == work_order.supplier_id,
                Equipment.is_active == True,
            ).first()
            if matched:
                if required_category_id is not None and matched.category_id != required_category_id:
                    raise HTTPException(status_code=400, detail="הכלי שנבחר אינו תואם לסוג שהוזמן")
                blocking_wo = _get_blocking_work_order(db, matched.id, work_order.id)
                if blocking_wo:
                    raise HTTPException(
                        status_code=400,
                        detail=f"הכלי שנבחר כבר משויך להזמנה פעילה אחרת (#{blocking_wo.order_number or blocking_wo.id})",
                    )
                resolved_equipment_id = matched.id
            else:
                # Auto-create equipment entry from supplier_equipment data
                from app.models.equipment import Equipment as Eq
                new_eq = Eq(
                    name=work_order.equipment_type or "כלי ספק",
                    license_plate=effective_plate,
                    supplier_id=work_order.supplier_id,
                    equipment_type=work_order.equipment_type,
                    type_id=requested_model.id if requested_model else None,
                    category_id=required_category_id,
                    status="available",
                    is_active=True,
                )
                db.add(new_eq)
                db.flush()
                resolved_equipment_id = new_eq.id
                logger.info(f"WO {work_order.id}: auto-created equipment id={new_eq.id} for plate={effective_plate}")

        # ── Update work order ───────────────────────────────────────
        work_order.status = "SUPPLIER_ACCEPTED_PENDING_COORDINATOR"
        work_order.supplier_response_at = datetime.utcnow()
        work_order.response_received_at = datetime.utcnow()
        work_order.equipment_id = resolved_equipment_id
        work_order.equipment_license_plate = effective_plate

        logger.info(
            f"WO {work_order.id}: supplier accepted — equipment_id={resolved_equipment_id}, "
            f"plate={effective_plate}, supplier={work_order.supplier_id}"
        )
        
        if request.notes:
            work_order.constraint_notes = f"הערות ספק: {request.notes}"
        
        if work_order.version is not None:
            work_order.version += 1
        
        db.commit()
        
        # Send notification to work manager
        _send_notification_to_manager(db, work_order, "accepted")
        
        return SupplierResponseResult(
            success=True,
            message="ההזמנה אושרה בהצלחה! מנהל העבודה יצור איתך קשר בקרוב.",
            order_number=work_order.order_number
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Portal accept error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה באישור ההזמנה"
        )


@router.post("/{portal_token}/reject", response_model=SupplierResponseResult)
def reject_work_order(
    portal_token: str,
    request: SupplierRejectRequest,
    db: Session = Depends(get_db)
):
    """
    דחיית הזמנת עבודה על ידי ספק
    Public endpoint - token-based access
    """
    # Find work order
    work_order = get_work_order_by_token(db, portal_token)
    
    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="הזמנה לא נמצאה"
        )
    
    # Check token validity
    is_valid, error_message = check_token_valid(work_order)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    try:
        # Update work order
        work_order.supplier_response_at = datetime.utcnow()
        work_order.response_received_at = datetime.utcnow()
        
        # Store rejection info
        if request.reason_id:
            work_order.rejection_reason_id = request.reason_id
        if request.notes:
            work_order.rejection_notes = request.notes
        
        # Increment version
        if work_order.version is not None:
            work_order.version += 1
        
        db.commit()
        
        # Send notification to work manager
        _send_notification_to_manager(db, work_order, "rejected")
        
        # If fair rotation, move to next supplier
        if not work_order.is_forced_selection:
            _move_to_next_supplier(db, work_order)
        else:
            # Forced selection - mark as rejected
            work_order.status = "REJECTED"
            db.commit()
        
        # Fair Rotation — update rejected supplier's score
        try:
            if work_order.supplier_id:
                from app.services.supplier_rotation_service import SupplierRotationService
                SupplierRotationService().update_rotation_after_rejection(db, supplier_id=work_order.supplier_id)
        except Exception as _re:
            logger.warning(f"Fair Rotation update on portal reject WO {work_order.id}: {_re}")

        return SupplierResponseResult(
            success=True,
            message="ההזמנה נדחתה. תודה על העדכון.",
            order_number=work_order.order_number
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Portal reject error WO: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בדחיית ההזמנה"
        )


@router.get("/{portal_token}/status")
def get_portal_status(
    portal_token: str,
    db: Session = Depends(get_db)
):
    """
    בדיקת סטטוס תוקף הטוקן
    Public endpoint for checking token validity
    """
    work_order = db.query(WorkOrder).filter(
        WorkOrder.portal_token == portal_token
    ).first()
    
    if not work_order:
        return {
            "is_valid": False,
            "is_expired": True,
            "message": "קישור לא תקין",
            "time_remaining_seconds": 0
        }
    
    is_valid, error_message = check_token_valid(work_order)
    
    # Calculate time remaining
    now = datetime.utcnow()
    expiry = work_order.portal_expiry or work_order.token_expires_at or work_order.portal_token_expires
    time_remaining = 0
    is_expired = False
    
    if expiry:
        if expiry > now:
            time_remaining = int((expiry - now).total_seconds())
        else:
            is_expired = True
    
    return {
        "is_valid": is_valid,
        "is_expired": is_expired,
        "message": error_message if not is_valid else "קישור תקין",
        "time_remaining_seconds": time_remaining,
        "status": work_order.status,
        "order_number": work_order.order_number
    }


# ============================================
# INTERNAL FUNCTIONS
# ============================================

def _send_notification_to_manager(db: Session, work_order: WorkOrder, action: str):
    """Send notification to work manager and coordinators about supplier response."""
    try:
        from app.services.notification_service import notify_supplier_accepted, notify
        from app.models.user import User
        region_id = getattr(getattr(work_order, "project", None), "region_id", None)

        action_text = "אושרה" if action == "accepted" else "נדחתה"
        supplier_name = work_order.supplier.name if work_order.supplier else "לא ידוע"
        wo_num = work_order.order_number or work_order.id

        # Notify coordinators on supplier acceptance
        if action == "accepted":
            notify_supplier_accepted(db, work_order)
        else:
            # Supplier rejected: notify creator and coordinators
            reject_msg = f"הזמנה #{wo_num} נדחתה על ידי {supplier_name}. הזמנה מועברת לספק הבא בסבב."
            creator_id = getattr(work_order, 'created_by', None) or getattr(work_order, 'created_by_id', None)
            if creator_id:
                notify(
                    db, creator_id,
                    title=f"ספק דחה הזמנה — {supplier_name}",
                    message=reject_msg,
                    notification_type="supplier_response",
                    entity_type="work_order",
                    entity_id=work_order.id,
                    priority="high",
                    action_url=f"/work-orders/{work_order.id}",
                )
            # Notify coordinators immediately
            from sqlalchemy import text
            coordinators = db.execute(text("""
                SELECT u.id FROM users u JOIN roles r ON u.role_id = r.id
                WHERE r.code IN ('ORDER_COORDINATOR', 'ADMIN') AND u.is_active = true
                  AND (:region_id IS NULL OR r.code = 'ADMIN' OR u.region_id = :region_id)
            """), {"region_id": region_id}).fetchall()
            for row in coordinators:
                if row[0] != creator_id:
                    notify(
                        db, row[0],
                        title=f"ספק דחה הזמנה #{wo_num}",
                        message=reject_msg,
                        notification_type="supplier_response",
                        entity_type="work_order",
                        entity_id=work_order.id,
                        priority="high",
                        action_url=f"/order-coordination",
                    )

        # Also send email (best-effort)
        try:
            from app.core.email import send_email
            if work_order.project and work_order.project.manager_id:
                manager = db.query(User).filter(User.id == work_order.project.manager_id).first()
                if manager and manager.email:
                    send_email(
                        to=manager.email,
                        subject=f"הזמנת עבודה {wo_num} {action_text}",
                        body=(
                            f"שלום {manager.first_name or 'מנהל'},\n\n"
                            f"הזמנה מספר {wo_num} {action_text} על ידי הספק {supplier_name}.\n\n"
                            f"בברכה,\nמערכת ניהול יערות Forewise"
                        ),
                    )
        except Exception:
            pass


        logging.getLogger(__name__).info(
            f"[Notification] Work order {wo_num} was {action} by supplier"
        )

    except Exception as e:

        logging.getLogger(__name__).warning(f"[Notification] Failed: {e}")


def _move_to_next_supplier(db: Session, work_order: WorkOrder):
    """Move to next supplier in fair rotation.
Hierarchy: area region REJECTED.
    Only selects suppliers who have equipment with a license plate.
    """
    try:
        import secrets
        
        if not work_order.project:
            logger.warning(f"Rotation: No project on WO {work_order.id}")
            return
        
        from app.models.supplier_rotation import SupplierRotation
        from app.models.equipment import Equipment
        
        area_id = work_order.project.area_id
        region_id = work_order.project.region_id
        
        # Get equipment type ID
        eq_type_id = getattr(work_order, 'equipment_type_id', None)
        if not eq_type_id and work_order.equipment_id:
            eq = db.query(Equipment).filter(Equipment.id == work_order.equipment_id).first()
            if eq:
                eq_type_id = getattr(eq, 'type_id', None)
        
        def find_supplier_with_equipment(filter_area_id=None, filter_region_id=None):
            """Find next supplier in rotation who actually has equipment with license plate."""
            query = db.query(SupplierRotation).join(
                Supplier, Supplier.id == SupplierRotation.supplier_id
            ).filter(
                SupplierRotation.is_active == True,
                SupplierRotation.is_available != False,
                SupplierRotation.supplier_id != work_order.supplier_id,
                Supplier.is_active == True,
            )
            if eq_type_id:
                query = query.filter(SupplierRotation.equipment_type_id == eq_type_id)
            if filter_area_id:
                query = query.filter(SupplierRotation.area_id == filter_area_id)
            elif filter_region_id:
                query = query.filter(SupplierRotation.region_id == filter_region_id)
            
            candidates = query.order_by(SupplierRotation.rotation_position.asc()).all()
            
            for rotation in candidates:
                # Check supplier has equipment with license plate for this type
                eq_check = db.query(Equipment).filter(
                    Equipment.supplier_id == rotation.supplier_id,
                    Equipment.is_active == True,
                    Equipment.license_plate != None,
                    Equipment.license_plate != '',
                )
                if eq_type_id:
                    eq_check = eq_check.filter(Equipment.type_id == eq_type_id)
                
                if eq_check.first():
                    return rotation
            
            return None
        
        next_rotation = None
        
        # Step 1: Try same AREA
        if area_id:
            next_rotation = find_supplier_with_equipment(filter_area_id=area_id)
            if next_rotation:
                pass
        
        # Step 2: Try same REGION (מרחב)
        if not next_rotation and region_id:
            next_rotation = find_supplier_with_equipment(filter_region_id=region_id)
            if next_rotation:
                pass
        
        # Step 3: No suppliers at all -> REJECTED + notify coordinator
        if not next_rotation:
            eq_type_name = work_order.equipment_type or f"type_id={eq_type_id}"
            work_order.status = "REJECTED"
            
            # Notify coordinators: no suppliers with equipment available
            try:
                from app.services.notification_service import notify
                from sqlalchemy import text
                region_id = getattr(getattr(work_order, "project", None), "region_id", None)
                coordinators = db.execute(text("""
                    SELECT u.id FROM users u JOIN roles r ON u.role_id = r.id
                    WHERE r.code IN ('ORDER_COORDINATOR', 'ADMIN') AND u.is_active = true
                      AND (:region_id IS NULL OR r.code = 'ADMIN' OR u.region_id = :region_id)
                """), {"region_id": region_id}).fetchall()
                wo_num = work_order.order_number or work_order.id
                for row in coordinators:
                    notify(
                        db, row[0],
                        title=f"אין ספקים זמינים — הזמנה #{wo_num}",
                        message=f"לא נמצא ספק עם כלי ומספר רישוי מסוג {eq_type_name} באזור או במרחב. ההזמנה עברה ל-REJECTED.",
                        notification_type="supplier_response",
                        entity_type="work_order",
                        entity_id=work_order.id,
                        priority="high",
                        action_url=f"/order-coordination",
                    )
            except Exception as ne:
                logger.warning(f"Rotation notification error: {ne}")
            
            db.commit()
            return
        
        # Update rotation stats for rejected supplier
        old_supplier_id = work_order.supplier_id
        old_rot_query = db.query(SupplierRotation).filter(
            SupplierRotation.supplier_id == old_supplier_id,
        )
        if area_id:
            old_rot_query = old_rot_query.filter(SupplierRotation.area_id == area_id)
        if eq_type_id:
            old_rot_query = old_rot_query.filter(SupplierRotation.equipment_type_id == eq_type_id)
        old_rotation = old_rot_query.first()
        if old_rotation:
            old_rotation.rejection_count = (old_rotation.rejection_count or 0) + 1

        # Update work order with new supplier
        work_order.supplier_id = next_rotation.supplier_id
        work_order.portal_token = secrets.token_urlsafe(32)
        work_order.portal_expiry = datetime.utcnow() + timedelta(hours=3)
        work_order.token_expires_at = work_order.portal_expiry
        work_order.supplier_response_at = None
        work_order.response_received_at = None
        work_order.rejection_reason_id = None
        work_order.rejection_notes = None

        # Update rotation stats for new supplier
        next_rotation.total_assignments = (next_rotation.total_assignments or 0) + 1
        next_rotation.last_assignment_date = datetime.utcnow().date()
        
        db.commit()
        
        logger.info(f"Rotation: moved from supplier {old_supplier_id} to {next_rotation.supplier_id}")
        
        # Send new order to next supplier
        _send_order_to_supplier(db, work_order)
        
    except Exception as e:
        logger.error(f"Failed to move to next supplier: {e}")
        db.rollback()


def _send_order_to_supplier(db: Session, work_order: WorkOrder):
    """Send order notification to supplier via SMS/Email"""
    try:
        from app.core.config import settings
        from app.core.email import send_email
        
        supplier = db.query(Supplier).filter(Supplier.id == work_order.supplier_id).first()
        if not supplier:
            return
        
        landing_url = f"{settings.FRONTEND_URL}/supplier-landing/{work_order.portal_token}"
        
        # Send email
        if supplier.email:
            send_email(
                to=supplier.email,
                subject=f"הזמנת עבודה חדשה - {work_order.order_number}",
                body=f"""
שלום {supplier.name},

קיבלת הזמנת עבודה חדשה מForewise.

פרטי ההזמנה:
• מספר הזמנה: {work_order.order_number}
• פרויקט: {work_order.project.name if work_order.project else 'לא ידוע'}
• סוג ציוד: {work_order.equipment_type or 'לא צוין'}
• תאריך התחלה: {work_order.work_start_date or 'לא צוין'}

לאישור או דחיית ההזמנה, לחץ על הקישור:
{landing_url}

שים לב: הקישור תקף ל-3 שעות בלבד.

בברכה,
מערכת ניהול יערות Forewise
"""
            )
        
        logger.info(f"Sent order to supplier {supplier.name}")

    except Exception as e:
        logger.error(f"Failed to send order to supplier: {e}")
