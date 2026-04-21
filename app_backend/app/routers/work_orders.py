"""
WorkOrders Router - API endpoints להזמנות עבודה
Handles HTTP requests with state machine support
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.models.work_order import WorkOrder
from app.models.project import Project
from app.models.budget import Budget
from app.models.equipment import Equipment
from app.services.notification_service import (
    notify_work_order_created,
    notify_work_order_approved,
    notify_work_order_rejected,
)
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderResponse,
    WorkOrderList,
    WorkOrderSearch,
    WorkOrderApproveRequest,
    WorkOrderRejectRequest,
    WorkOrderStatistics
)
from app.services.work_order_service import WorkOrderService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

# Create router
router = APIRouter(prefix="/work-orders", tags=["Work Orders"])

# Service instance
work_order_service = WorkOrderService()


class RemoveEquipmentResponse(BaseModel):
    """תוצאת הסרת כלי — שחרור תקציב מוקפא + סטטוס STOPPED"""

    released_amount: float = Field(..., description="סכום ששוחרר מהתקציב המחויב")
    work_order: WorkOrderResponse


class WorkOrderAllocationPreviewRequest(BaseModel):
    project_id: int
    equipment_type: str
    allocation_method: str = "FAIR_ROTATION"
    supplier_id: Optional[int] = None


def _enrich_hours(work_order, db: Session) -> dict:
    """Compute used/remaining hours from non-rejected worklogs."""
    from sqlalchemy import text
    try:
        row = db.execute(text("""
            SELECT COALESCE(SUM(work_hours), 0) as used
            FROM worklogs
            WHERE work_order_id = :wid AND UPPER(status) != 'REJECTED'
              AND is_active = true
        """), {"wid": work_order.id}).first()
        used = float(row.used) if row and row.used else 0.0
        estimated = float(work_order.estimated_hours or 0)
        remaining = max(estimated - used, 0)
        return {
            "used_hours": used,
            "remaining_hours": remaining,
            "days_total": round(estimated / 9, 1) if estimated else None,
            "days_used": round(used / 9, 1),
            "days_remaining": round(remaining / 9, 1),
        }
    except Exception:
        return {}


def _require_order_coordinator_or_admin(current_user: User) -> None:
    role_code = getattr(getattr(current_user, "role", None), "code", None) or getattr(current_user, "role_code", None)
    if role_code not in ("ADMIN", "SUPER_ADMIN", "ORDER_COORDINATOR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="פעולה זו מותרת רק למתאם הזמנות או מנהל מערכת",
        )


def _to_response(work_order, db: Session) -> dict:
    """Serialize WorkOrder ORM object + inject computed hours + equipment license plate."""
    from sqlalchemy import text as sa_text
    d = WorkOrderResponse.model_validate(work_order).model_dump()
    d.update(_enrich_hours(work_order, db))
    # Inject equipment license_plate if not already set
    if not d.get('equipment_license_plate') and work_order.equipment_id:
        try:
            row = db.execute(
                sa_text("SELECT license_plate FROM equipment WHERE id=:eid"),
                {"eid": work_order.equipment_id}
            ).first()
            if row:
                d['equipment_license_plate'] = row[0]
        except Exception:
            pass
    return d


@router.get("", response_model=WorkOrderList)
def list_work_orders(
    search: Annotated[WorkOrderSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    List work orders with filters and pagination
    
    Permissions: work_orders.read
    """
    require_permission(current_user, "work_orders.read")
    
    if current_user.area_id is not None:
        search.area_id = current_user.area_id

    try:
        work_orders, total = work_order_service.list(db, search)
        
        total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
        
        enriched = [_to_response(wo, db) for wo in work_orders]
        return WorkOrderList(
            items=enriched,
            total=total,
            page=search.page,
            page_size=search.page_size,
            total_pages=total_pages
        )
    
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.get("/statistics", response_model=WorkOrderStatistics)
def get_work_order_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_id: Optional[int] = Query(None, description="Filter by project"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier")
):
    """
    Get work order statistics

    Permissions: work_orders.read
    """
    require_permission(current_user, "work_orders.read")

    try:
        filters = {}
        if project_id:
            filters['project_id'] = project_id
        if supplier_id:
            filters['supplier_id'] = supplier_id

        stats = work_order_service.get_statistics(db, filters)
        return stats

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.post("/preview-allocation")
def preview_work_order_allocation(
    data: WorkOrderAllocationPreviewRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Preview which supplier the backend would choose for a work order."""
    require_permission(current_user, "work_orders.create")

    try:
        return work_order_service.preview_supplier_selection(
            db=db,
            project_id=data.project_id,
            equipment_type=data.equipment_type,
            allocation_method=data.allocation_method,
            supplier_id=data.supplier_id,
        )
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.get("/{work_order_id}", response_model=WorkOrderResponse)
def get_work_order(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get work order by ID

    Permissions: work_orders.read
    """
    require_permission(current_user, "work_orders.read")

    try:
        query = (
            select(WorkOrder)
            .join(Project, Project.id == WorkOrder.project_id)
            .where(
                WorkOrder.id == work_order_id,
                WorkOrder.deleted_at.is_(None),
            )
        )

        role_code = (current_user.role.code if current_user.role else '').upper()
        if current_user.area_id is not None and role_code not in ('ADMIN', 'SUPER_ADMIN', 'WORK_MANAGER', 'ORDER_COORDINATOR', 'ACCOUNTANT'):
            query = query.where(Project.area_id == current_user.area_id)

        work_order = db.execute(query).scalar_one_or_none()
        if not work_order:
            raise HTTPException(status_code=404, detail="WorkOrder not found")

        return _to_response(work_order, db)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.post("", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
def create_work_order(
    data: WorkOrderCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Create new work order
    
    Permissions: work_orders.create
    """
    require_permission(current_user, "work_orders.create")
    
    try:
        work_order = work_order_service.create(db, data, current_user_id=current_user.id)
        notify_work_order_created(db, work_order)
        try:
            from app.services.activity_logger import log_work_order_created
            log_work_order_created(db, work_order_id=work_order.id, user_id=current_user.id,
                                   project_id=work_order.project_id)
        except Exception:
            pass
        return work_order
    
    except HTTPException:
        raise  # pass-through 400/422/404 etc from service layer
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.put("/{work_order_id}", response_model=WorkOrderResponse)
def update_work_order(
    work_order_id: int,
    data: WorkOrderUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Update work order
    
    Permissions: work_orders.update
    """
    require_permission(current_user, "work_orders.update")
    
    try:
        work_order = work_order_service.update(db, work_order_id, data, current_user_id=current_user.id)
        return work_order
    
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.delete("/{work_order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_order(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Delete work order (soft delete) + activity log
    
    Permissions: work_orders.delete
    """
    require_permission(current_user, "work_orders.delete")
    
    try:
        # Fetch order details before deletion for activity log
        work_order = work_order_service.get_work_order(db, work_order_id)
        if not work_order:
            raise NotFoundException(f"Work order {work_order_id} not found")
        
        order_number = getattr(work_order, 'order_number', work_order_id)
        admin_name = getattr(current_user, 'full_name', None) or getattr(current_user, 'username', f'User {current_user.id}')
        
        # Soft delete
        work_order_service.soft_delete(db, work_order_id, current_user_id=current_user.id)
        
        # Write activity log (non-critical)
        try:
            from sqlalchemy import text as sql_text
            db.execute(sql_text("""
                INSERT INTO activity_logs (action, activity_type, entity_type, entity_id, user_id, description)
                VALUES ('work_order.deleted', 'delete', 'work_order', :entity_id, :user_id, :description)
            """), {
                "entity_id": work_order_id,
                "user_id": current_user.id,
                "description": f"הזמנה מספר {order_number} נמחקה על ידי {admin_name}",
            })
            db.commit()
        except Exception as log_err:
            import logging
            logging.getLogger(__name__).warning(f"Activity log failed for delete {work_order_id}: {log_err}")
        
        return None
    
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.post("/{work_order_id}/restore", response_model=WorkOrderResponse)
def restore_work_order(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Restore soft-deleted work order
    
    Permissions: work_orders.restore
    """
    require_permission(current_user, "work_orders.restore")
    
    try:
        work_order = work_order_service.restore(db, work_order_id, current_user_id=current_user.id)
        return work_order
    
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.post("/{work_order_id}/approve", response_model=WorkOrderResponse)
def approve_work_order(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    request: Optional[WorkOrderApproveRequest] = None,
):
    """
    Approve work order
    
    Business Rule: equipment_id is REQUIRED for approval!
    
    Permissions: work_orders.approve
    """
    require_permission(current_user, "work_orders.approve")
    _require_order_coordinator_or_admin(current_user)
    
    try:
        # Service handles: status transition + supplier email + work-manager email
        # + project-manager in-app notification.
        # Router adds: in-app notification to the creator (so they know their
        # request was approved). No additional broadcast — the previous code
        # spammed every coordinator/admin/area/work manager in the system with
        # an "approved" email, which created notification fatigue.
        work_order = work_order_service.approve(
            db, work_order_id,
            request or WorkOrderApproveRequest(),
            current_user_id=current_user.id,
        )
        notify_work_order_approved(db, work_order)
        return work_order
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.post("/{work_order_id}/reject", response_model=WorkOrderResponse)
def reject_work_order(
    work_order_id: int,
    request: WorkOrderRejectRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Reject work order
    
    Permissions: work_orders.approve (same as approve)
    """
    require_permission(current_user, "work_orders.approve")
    _require_order_coordinator_or_admin(current_user)
    
    try:
        work_order = work_order_service.reject(db, work_order_id, request, current_user_id=current_user.id)
        reason = getattr(request, 'reason', '') or getattr(request, 'notes', '') or ''
        notify_work_order_rejected(db, work_order, reason=reason)
        return work_order
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.post("/{work_order_id}/cancel", response_model=WorkOrderResponse)
def cancel_work_order(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    notes: Optional[str] = None,
    version: Optional[int] = None
):
    """
    Cancel work order
    
    Permissions: work_orders.cancel
    """
    require_permission(current_user, "work_orders.cancel")
    
    try:
        work_order = work_order_service.cancel(db, work_order_id, notes, version, current_user_id=current_user.id)
        return work_order
    
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.post("/{work_order_id}/close", response_model=WorkOrderResponse)
def close_work_order(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    actual_hours: Optional[float] = None,
    version: Optional[int] = None
):
    """
    Close/Complete work order

    Permissions: work_orders.close
    """
    require_permission(current_user, "work_orders.close")

    try:
        from decimal import Decimal
        actual_hours_decimal = Decimal(str(actual_hours)) if actual_hours else None
        work_order = work_order_service.close(db, work_order_id, actual_hours_decimal, version, current_user_id=current_user.id)
        # Activity log is handled in service
        return work_order
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


# ============================================
# FRONTEND COMPATIBILITY ALIASES
# These endpoints provide backwards compatibility
# with the frontend's expected methods/routes
# ============================================

@router.patch("/{work_order_id}", response_model=WorkOrderResponse)
def patch_work_order(
    work_order_id: int,
    data: WorkOrderUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    PATCH alias for PUT - Frontend compatibility
    """
    return update_work_order(work_order_id, data, db, current_user)


@router.patch("/{work_order_id}/approve", response_model=WorkOrderResponse)
def patch_approve_work_order(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    request: Optional[WorkOrderApproveRequest] = None
):
    """
    PATCH alias for POST approve - Frontend compatibility
    """
    if request is None:
        request = WorkOrderApproveRequest()
    return approve_work_order(work_order_id, db, current_user, request)


@router.patch("/{work_order_id}/reject", response_model=WorkOrderResponse)
def patch_reject_work_order(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    request: Optional[WorkOrderRejectRequest] = None
):
    """
    PATCH alias for POST reject - Frontend compatibility
    """
    if request is None:
        request = WorkOrderRejectRequest()
    return reject_work_order(work_order_id, request, db, current_user)


@router.patch("/{work_order_id}/start", response_model=WorkOrderResponse)
@router.post("/{work_order_id}/start", response_model=WorkOrderResponse)
def start_work_order(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Start work order (transition to in_progress status)
    
    Permissions: work_orders.update
    """
    require_permission(current_user, "work_orders.update")
    
    try:
        work_order = work_order_service.start(db, work_order_id, current_user.id)
        # Activity log is handled in service
        return work_order
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.patch("/{work_order_id}/complete", response_model=WorkOrderResponse)
@router.post("/{work_order_id}/complete", response_model=WorkOrderResponse)
def complete_work_order(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    actual_hours: Optional[float] = None
):
    """
    Complete work order - alias for close
    
    Permissions: work_orders.close
    """
    return close_work_order(work_order_id, db, current_user, actual_hours, None)


# ============================================
# COORDINATION ENDPOINTS
# For Order Coordinator role
# ============================================

@router.post("/{work_order_id}/send-to-supplier")
def send_work_order_to_supplier(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Send work order to supplier via portal link.
    Generates portal_token (3h TTL) and sends email.
    Returns: { portal_token, portal_url, expires_at, work_order_id, status }
    Only ORDER_COORDINATOR and ADMIN may distribute work orders.
    """
    require_permission(current_user, "work_orders.distribute")
    _require_order_coordinator_or_admin(current_user)

    try:
        result = work_order_service.send_to_supplier(db, work_order_id, current_user.id)
        wo = result["work_order"]
        email_sent = result.get("email_sent", False)
        supplier_name = result.get("supplier_name", "ספק")
        msg = f"ההזמנה נשלחה ל{supplier_name}."
        if email_sent:
            msg += " מייל עם קישור נשלח בהצלחה. הקישור תקף ל-3 שעות."
        else:
            msg += " שים לב: לא נשלח מייל — ודא שלספק יש כתובת אימייל."
        return {
            "portal_token": result["portal_token"],
            "portal_url": result["portal_url"],
            "expires_at": result["expires_at"],
            "work_order_id": wo.id,
            "supplier_id": wo.supplier_id,
            "supplier_name": supplier_name,
            "status": wo.status,
            "email_sent": email_sent,
            "message": msg,
        }
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.post("/{work_order_id}/move-to-next-supplier", response_model=WorkOrderResponse)
def move_to_next_supplier(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Move work order to next supplier in fair rotation
    
    Permissions: work_orders.coordinate
    """
    require_permission(current_user, "work_orders.update")
    _require_order_coordinator_or_admin(current_user)
    
    try:
        work_order = work_order_service.move_to_next_supplier(db, work_order_id, current_user.id)
        return work_order
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.post("/{work_order_id}/resend-to-supplier", response_model=WorkOrderResponse)
def resend_to_supplier(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Resend work order to current supplier (extend portal token)
    
    Permissions: work_orders.coordinate
    """
    require_permission(current_user, "work_orders.update")
    _require_order_coordinator_or_admin(current_user)
    
    try:
        work_order = work_order_service.resend_to_supplier(db, work_order_id, current_user.id)
        return work_order
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.post("/{work_order_id}/remove-equipment", response_model=RemoveEquipmentResponse)
def remove_equipment_from_project(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Remove equipment from project — release remaining frozen budget, free equipment, STOPPED."""
    require_permission(current_user, "work_orders.update")

    try:
        work_order = work_order_service.get_work_order(db, work_order_id)
        if not work_order:
            raise HTTPException(status_code=404, detail="הזמנה לא נמצאה")

        budget = None
        if work_order.project_id:
            budget = (
                db.query(Budget)
                .filter(
                    Budget.project_id == work_order.project_id,
                    Budget.is_active.is_(True),
                    Budget.deleted_at.is_(None),
                )
                .first()
            )

        remaining = float(work_order.remaining_frozen or 0)
        released = 0.0
        if remaining > 0:
            released = remaining
            if budget is not None:
                committed = float(budget.committed_amount or 0)
                new_committed = max(0.0, committed - remaining)
                budget.committed_amount = new_committed
                total = float(budget.total_amount or 0)
                spent = float(budget.spent_amount or 0)
                budget.remaining_amount = max(total - new_committed - spent, 0.0)
            work_order.remaining_frozen = Decimal(0)
            work_order.frozen_amount = Decimal(0)

        if work_order.equipment_id:
            eq = db.query(Equipment).filter(Equipment.id == work_order.equipment_id).first()
            if eq:
                eq.assigned_project_id = None
            work_order.equipment_id = None

        # Clear equipment-related fields (if columns exist on model)
        if hasattr(work_order, 'equipment_scan'):
            work_order.equipment_scan = None
        if hasattr(work_order, 'license_plate'):
            work_order.license_plate = None

        work_order.status = "STOPPED"
        work_order.updated_at = datetime.utcnow()

        admin_name = (
            getattr(current_user, "full_name", None)
            or getattr(current_user, "username", None)
            or f"User {current_user.id}"
        )
        try:
            from sqlalchemy import text as sql_text

            db.execute(
                sql_text(
                    """
                    INSERT INTO activity_logs (action, activity_type, entity_type, entity_id, user_id, description)
                    VALUES ('WORK_ORDER_EQUIPMENT_REMOVED', 'update', 'work_order', :eid, :uid, :description)
                    """
                ),
                {
                    "eid": work_order_id,
                    "uid": current_user.id,
                    "description": (
                        f"הוסר כלי מהזמנה {work_order.order_number or work_order_id}; "
                        f"שוחררו {released:,.0f} מהתקציב — {admin_name}"
                    ),
                },
            )
        except Exception as log_err:
            import logging

            logging.getLogger(__name__).warning(
                f"Activity log failed for remove-equipment {work_order_id}: {log_err}"
            )

        db.commit()
        db.refresh(work_order)

        try:
            from app.services.notification_service import notify
            from sqlalchemy import text

            coordinators = db.execute(
                text(
                    """
                SELECT u.id FROM users u JOIN roles r ON u.role_id=r.id
                WHERE r.code IN ('ORDER_COORDINATOR','ADMIN','ACCOUNTANT') AND u.is_active=true
                  AND (:region_id IS NULL OR r.code IN ('ADMIN','ACCOUNTANT') OR u.region_id = :region_id)
            """
                ),
                {"region_id": getattr(getattr(work_order, "project", None), "region_id", None)},
            ).fetchall()
            wo_num = work_order.order_number or work_order.id
            for row in coordinators:
                notify(
                    db,
                    row[0],
                    title=f"כלי הוסר מפרויקט — הזמנה #{wo_num}",
                    message=f"יתרה תקציבית {released:,.0f} שוחררה",
                    notification_type="work_order",
                    entity_type="work_order",
                    entity_id=work_order.id,
                    priority="medium",
                )
        except Exception:
            pass

        return RemoveEquipmentResponse(
            released_amount=released,
            work_order=WorkOrderResponse.model_validate(_to_response(work_order, db)),
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="שגיאת שרת")


# ============================================
# QR SCAN ENDPOINTS (Task 7) — 3 Scenarios
# ============================================

def _normalize_plate(value: Optional[str]) -> str:
    """Canonical license-plate form: trimmed, upper-cased, single-space-collapsed.

    Used everywhere a plate is compared or stored so that '123-45-678 ',
    '123-45-678' and ' 123-45-678' all match.
    """
    if not value:
        return ""
    return " ".join(value.strip().upper().split())


class ScanEquipmentRequest(BaseModel):
    license_plate: str = Field(..., description="מספר רישוי שנסרק")

class ConfirmEquipmentRequest(BaseModel):
    equipment_id: int = Field(..., description="מזהה כלי לאישור")

class AdminOverrideEquipmentRequest(BaseModel):
    license_plate: str = Field(..., description="מספר רישוי לאישור חריג")
    reason: str = Field(..., description="סיבת אישור חריג")


def _release_equipment_from_old_wo(db: Session, equipment: Equipment, exclude_wo_id: int, actor_id: int):
    """
    If equipment is currently assigned to another WO, release it:
    - Keep already-reported hours/budget (spent stays)
    - Release remaining frozen budget back to project
    - Mark old WO as STOPPED
    """
    from sqlalchemy import text as sql_text

    old_wos = (
        db.query(WorkOrder)
        .filter(
            WorkOrder.equipment_id == equipment.id,
            WorkOrder.id != exclude_wo_id,
            WorkOrder.status.in_(["APPROVED_AND_SENT", "IN_PROGRESS", "ACTIVE"]),
        )
        .all()
    )

    released_details = []
    for old_wo in old_wos:
        remaining = float(old_wo.remaining_frozen or 0)
        released = 0.0

        if remaining > 0:
            released = remaining
            if old_wo.project_id:
                budget = (
                    db.query(Budget)
                    .filter(
                        Budget.project_id == old_wo.project_id,
                        Budget.is_active.is_(True),
                        Budget.deleted_at.is_(None),
                    )
                    .first()
                )
                if budget:
                    committed = float(budget.committed_amount or 0)
                    new_committed = max(0.0, committed - remaining)
                    budget.committed_amount = new_committed
                    total = float(budget.total_amount or 0)
                    spent = float(budget.spent_amount or 0)
                    budget.remaining_amount = max(total - new_committed - spent, 0.0)

            old_wo.remaining_frozen = Decimal(0)

        old_wo.equipment_id = None
        old_wo.equipment_license_plate = None
        old_wo.status = "STOPPED"
        old_wo.updated_at = datetime.utcnow()

        try:
            db.execute(
                sql_text("""
                    INSERT INTO activity_logs (action, activity_type, entity_type, entity_id, user_id, description)
                    VALUES ('EQUIPMENT_TRANSFERRED', 'update', 'work_order', :eid, :uid, :desc)
                """),
                {
                    "eid": old_wo.id,
                    "uid": actor_id,
                    "desc": (
                        f"כלי {equipment.license_plate} הועבר לפרויקט אחר; "
                        f"שוחררו {released:,.0f} מהתקציב; הזמנה {old_wo.order_number or old_wo.id} עוצרה"
                    ),
                },
            )
        except Exception:
            pass

        released_details.append({
            "old_wo_id": old_wo.id,
            "old_wo_number": old_wo.order_number,
            "released_amount": released,
        })

    return released_details


@router.post("/{work_order_id}/scan-equipment")
def scan_equipment(
    work_order_id: int,
    body: ScanEquipmentRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Scan equipment QR/license plate and match against work order.
    3 scenarios:
      A) Full match — plate + type match → auto-approve
      B) Same type, different plate → return question for user confirmation
      C) Wrong type → block (only Admin can override via separate endpoint)
    """
    require_permission(current_user, "work_orders.read")

    license_plate = _normalize_plate(body.license_plate)
    if not license_plate:
        raise HTTPException(status_code=400, detail="מספר רישוי ריק")

    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="הזמנה לא נמצאה")

    # Block scan if WO not yet approved for execution
    from app.core.enums import WO_EXECUTION
    if (wo.status or '').upper() not in WO_EXECUTION:
        raise HTTPException(status_code=400, detail="לא ניתן לסרוק כלי — ההזמנה טרם אושרה ע״י מתאם הזמנות")

    expected_plate = _normalize_plate(wo.equipment_license_plate)
    if not expected_plate and wo.equipment_id:
        eq = db.query(Equipment).filter(Equipment.id == wo.equipment_id).first()
        if eq:
            expected_plate = _normalize_plate(eq.license_plate)

    scanned_eq = (
        db.query(Equipment)
        .filter(Equipment.license_plate.ilike(license_plate))
        .first()
    )

    # ── Scenario A: Full match ──
    if license_plate == expected_plate:
        if scanned_eq:
            wo.equipment_id = scanned_eq.id
            # write back the canonical form to Equipment too
            scanned_eq.license_plate = license_plate
        wo.equipment_license_plate = license_plate
        wo.updated_at = datetime.utcnow()
        if wo.status in ("APPROVED_AND_SENT",):
            wo.status = "IN_PROGRESS"
        db.commit()
        db.refresh(wo)
        return {
            "status": "ok",
            "message": "כלי תואם — אומת בהצלחה",
            "work_order": _to_response(wo, db),
        }

    # ── Scenario B: Same type, different plate ──
    wo_type = (wo.equipment_type or "").strip().lower()
    scanned_type = (scanned_eq.equipment_type if scanned_eq else "").strip().lower()

    if scanned_eq and wo_type and scanned_type == wo_type:
        old_project_info = None
        old_wos = (
            db.query(WorkOrder)
            .filter(
                WorkOrder.equipment_id == scanned_eq.id,
                WorkOrder.id != work_order_id,
                WorkOrder.status.in_(["APPROVED_AND_SENT", "IN_PROGRESS", "ACTIVE"]),
            )
            .all()
        )
        if old_wos:
            from sqlalchemy import text as sql_text
            for ow in old_wos:
                proj_name = None
                if ow.project_id:
                    row = db.execute(sql_text("SELECT name FROM projects WHERE id=:pid"), {"pid": ow.project_id}).first()
                    proj_name = row[0] if row else None
                old_project_info = {
                    "wo_id": ow.id,
                    "wo_number": ow.order_number,
                    "project_name": proj_name,
                    "remaining_hours": float(ow.remaining_frozen or 0) / float(ow.hourly_rate or 1) if ow.hourly_rate else 0,
                }

        return {
            "status": "different_plate",
            "message": f"הכלי שנסרק ({license_plate}) שונה ממספר הרישוי בהזמנה ({expected_plate or 'לא הוגדר'})",
            "question": "הכלי שנסרק שונה ממספר הרישוי בהזמנה. האם לשייך לפרויקט?",
            "equipment_id": scanned_eq.id,
            "equipment_type": scanned_eq.equipment_type,
            "old_project": old_project_info,
        }

    # ── Scenario C: Wrong type → BLOCK + return WO to coordinator ──
    is_admin = bool(current_user.role and current_user.role.code in ("ADMIN", "SUPER_ADMIN"))
    ordered_type = wo.equipment_type or "לא ידוע"
    scanned_type_label = scanned_eq.equipment_type if scanned_eq else "לא ידוע"
    previous_status = wo.status

    # Move ownership back to the coordinator. Field operations (scan / worklog)
    # are blocked until the coordinator re-decides (re-distribute / override / cancel).
    wo.status = "NEEDS_RE_COORDINATION"
    wo.updated_at = datetime.utcnow()

    # Audit log — explain WHY the WO bounced back, with both types and the user.
    audit_desc = (
        f"קליטת כלי נחסמה — סוג הכלי שנסרק ({scanned_type_label}) "
        f"שונה מהמוזמן ({ordered_type}). מספר רישוי שנסרק: {license_plate}. "
        f"ההזמנה הוחזרה למתאם הזמנות (סטטוס קודם: {previous_status})."
    )
    try:
        from sqlalchemy import text as _sql_text
        db.execute(
            _sql_text(
                "INSERT INTO activity_logs"
                " (action, activity_type, entity_type, entity_id, user_id, description, category)"
                " VALUES ('WRONG_EQUIPMENT_BLOCKED', 'update', 'work_order', :eid, :uid, :desc, 'operational')"
            ),
            {"eid": work_order_id, "uid": current_user.id, "desc": audit_desc},
        )
    except Exception:
        pass

    db.commit()
    db.refresh(wo)

    # Notify coordinator(s) for this WO's region/area
    try:
        from app.services.notification_service import notify_users_by_role
        notify_users_by_role(
            db,
            roles=["ORDER_COORDINATOR", "ADMIN"],
            title="הזמנה הוחזרה לטיפול — סוג כלי שגוי",
            body=audit_desc,
            link=f"/work-orders/{work_order_id}",
            region_id=getattr(wo, "region_id", None),
            area_id=getattr(wo, "area_id", None),
        )
    except Exception:
        # Notifications are best-effort — don't fail the request
        pass

    return {
        "status": "wrong_type",
        "message": "סוג הציוד שנסרק שונה מההזמנה — ההזמנה הוחזרה למתאם הזמנות",
        "ordered_type": ordered_type,
        "scanned_type": scanned_type_label,
        "admin_can_override": is_admin,
        "equipment_id": scanned_eq.id if scanned_eq else None,
        "wo_status": wo.status,
        "previous_status": previous_status,
    }


@router.post("/{work_order_id}/confirm-equipment")
def confirm_equipment(
    work_order_id: int,
    body: ConfirmEquipmentRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Confirm equipment assignment after scenario B (same type, different plate).
    - Assigns equipment to this WO
    - If equipment was in another active WO → release remaining budget there, stop that WO
    """
    require_permission(current_user, "work_orders.update")

    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="הזמנה לא נמצאה")

    eq = db.query(Equipment).filter(Equipment.id == body.equipment_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="ציוד לא נמצא")

    # Validate same type
    wo_type = (wo.equipment_type or "").strip().lower()
    eq_type = (eq.equipment_type or "").strip().lower()
    if wo_type and eq_type and wo_type != eq_type:
        raise HTTPException(status_code=400, detail="סוג הכלי אינו תואם להזמנה. נדרש אישור מנהל מערכת.")

    # Release from old project if needed
    released = _release_equipment_from_old_wo(db, eq, exclude_wo_id=work_order_id, actor_id=current_user.id)

    # Assign to current WO with normalized plate
    canonical_plate = _normalize_plate(eq.license_plate)
    eq.license_plate = canonical_plate
    wo.equipment_id = eq.id
    wo.equipment_license_plate = canonical_plate
    wo.updated_at = datetime.utcnow()
    if wo.status in ("APPROVED_AND_SENT",):
        wo.status = "IN_PROGRESS"

    db.commit()
    db.refresh(wo)

    msg = f"כלי {canonical_plate} שויך להזמנה בהצלחה"
    if released:
        old_nums = ", ".join(str(r["old_wo_number"] or r["old_wo_id"]) for r in released)
        msg += f" (הוסר מהזמנות: {old_nums})"

    return {
        "status": "ok",
        "message": msg,
        "released_from": released,
        "work_order": _to_response(wo, db),
    }


@router.post("/{work_order_id}/admin-override-equipment")
def admin_override_equipment(
    work_order_id: int,
    body: AdminOverrideEquipmentRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Admin-only: override equipment type mismatch (scenario C).
    Requires reason documentation.
    """
    is_admin = current_user.role and current_user.role.code in ("ADMIN", "SUPER_ADMIN")
    if not is_admin:
        raise HTTPException(status_code=403, detail="רק מנהל מערכת יכול לאשר חריגת סוג כלי")

    if not body.reason or not body.reason.strip():
        raise HTTPException(status_code=400, detail="חובה לציין סיבה לאישור חריג")

    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="הזמנה לא נמצאה")

    license_plate = _normalize_plate(body.license_plate)
    if not license_plate:
        raise HTTPException(status_code=400, detail="מספר רישוי ריק")

    eq = (
        db.query(Equipment)
        .filter(Equipment.license_plate.ilike(license_plate))
        .first()
    )

    # Release from old project if needed
    released = []
    if eq:
        released = _release_equipment_from_old_wo(db, eq, exclude_wo_id=work_order_id, actor_id=current_user.id)
        wo.equipment_id = eq.id
        eq.license_plate = license_plate  # canonicalize stored form

    wo.equipment_license_plate = license_plate
    wo.updated_at = datetime.utcnow()
    if wo.status in ("APPROVED_AND_SENT",):
        wo.status = "IN_PROGRESS"

    # Log the admin override
    from sqlalchemy import text as sql_text
    try:
        db.execute(
            sql_text("""
                INSERT INTO activity_logs (action, activity_type, entity_type, entity_id, user_id, description, category)
                VALUES ('ADMIN_EQUIPMENT_OVERRIDE', 'update', 'work_order', :eid, :uid, :desc, 'management')
            """),
            {
                "eid": work_order_id,
                "uid": current_user.id,
                "desc": (
                    f"אישור חריג: כלי {license_plate} (סוג: {eq.equipment_type if eq else 'לא ידוע'}) "
                    f"שויך להזמנה {wo.order_number or wo.id} (סוג נדרש: {wo.equipment_type or 'לא ידוע'}). "
                    f"סיבה: {body.reason.strip()}"
                ),
            },
        )
    except Exception:
        pass

    db.commit()
    db.refresh(wo)

    return {
        "status": "ok",
        "message": f"אישור חריג — כלי {license_plate} שויך להזמנה",
        "released_from": released,
        "work_order": _to_response(wo, db),
    }


# ============================================
# PDF ENDPOINT (Task 17)
# ============================================

def _build_work_order_html(wo, db: Session) -> str:
    """Build printable HTML for work order PDF."""
    from app.templates.email_worklog import LOGO_SVG

    project_name = ""
    if wo.project_id:
        from sqlalchemy import text as sa_text
        row = db.execute(sa_text("SELECT name FROM projects WHERE id=:pid"), {"pid": wo.project_id}).first()
        if row:
            project_name = row[0] or ""

    supplier_name = ""
    if wo.supplier_id:
        from sqlalchemy import text as sa_text
        row = db.execute(sa_text("SELECT name FROM suppliers WHERE id=:sid"), {"sid": wo.supplier_id}).first()
        if row:
            supplier_name = row[0] or ""

    eq_info = ""
    if wo.equipment_id:
        from sqlalchemy import text as sa_text
        row = db.execute(sa_text("SELECT name, license_plate, equipment_type FROM equipment WHERE id=:eid"),
                         {"eid": wo.equipment_id}).first()
        if row:
            eq_info = f"{row[2] or row[0] or ''}"
            if row[1]:
                eq_info += f" | {row[1]}"

    status_labels = {
        'PENDING': ('ממתין לאישור', '#854d0e', '#fef9c3'),
        'DISTRIBUTING': ('בהפצה לספקים', '#854d0e', '#fef9c3'),
        'APPROVED': ('מאושר', '#166534', '#dcfce7'),
        'APPROVED_AND_SENT': ('אושר ונשלח', '#166534', '#dcfce7'),
        'ACTIVE': ('פעיל', '#166534', '#dcfce7'),
        'IN_PROGRESS': ('בביצוע', '#1e40af', '#dbeafe'),
        'COMPLETED': ('הושלם', '#374151', '#e5e7eb'),
        'REJECTED': ('נדחה', '#991b1b', '#fee2e2'),
        'CANCELLED': ('בוטל', '#991b1b', '#fee2e2'),
        'STOPPED': ('הופסק', '#991b1b', '#fee2e2'),
    }
    sl = status_labels.get(wo.status or '', ('לא ידוע', '#374151', '#e5e7eb'))
    status_badge = f'<span style="background:{sl[2]};color:{sl[1]};padding:4px 14px;border-radius:20px;font-weight:700;font-size:14px;">{sl[0]}</span>'

    def fmt_date(d):
        if not d:
            return "—"
        return str(d)

    def fmt_currency(v):
        if not v:
            return "—"
        return f"{float(v):,.0f}"

    hours_data = _enrich_hours(wo, db)
    used_hours = hours_data.get("used_hours", 0)
    remaining_hours = hours_data.get("remaining_hours", 0)

    rows = [
        ("מספר הזמנה", wo.order_number or wo.id),
        ("כותרת", wo.title or "—"),
        ("סטטוס", status_badge),
        ("פרויקט", project_name or "—"),
        ("ספק", supplier_name or "—"),
        ("ציוד", eq_info or wo.equipment_type or "—"),
        ("תאריך התחלה", fmt_date(wo.work_start_date)),
        ("תאריך סיום", fmt_date(wo.work_end_date)),
        ("שעות מוערכות", float(wo.estimated_hours) if wo.estimated_hours else "—"),
        ("שעות שנוצלו", round(used_hours, 1)),
        ("שעות נותרות", round(remaining_hours, 1)),
        ("תעריף שעתי", fmt_currency(wo.hourly_rate)),
        ("סכום מוקפא", fmt_currency(wo.frozen_amount)),
        ("יתרת הקפאה", fmt_currency(wo.remaining_frozen)),
        ("עדיפות", wo.priority or "—"),
        ("תיאור", wo.description or "—"),
    ]

    table_rows = ""
    for i, (label, value) in enumerate(rows):
        bg = "background:#f8fbf9;" if i % 2 == 0 else ""
        table_rows += f'<tr style="{bg}"><td style="padding:10px 16px;font-size:13px;color:#6b7c72;width:35%;border-bottom:1px solid #eee;">{label}</td><td style="padding:10px 16px;font-size:14px;color:#111;border-bottom:1px solid #eee;">{value}</td></tr>'

    return f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
<meta charset="UTF-8">
<title>הזמנת עבודה #{wo.order_number or wo.id}</title>
<style>
  @media print {{
    .no-print {{ display: none !important; }}
    body {{ margin: 0; }}
  }}
  body {{ font-family: Heebo, Arial, sans-serif; background: #fff; color: #111; margin: 0; padding: 20px; }}
  .container {{ max-width: 700px; margin: 0 auto; }}
</style>
</head>
<body>
<div class="container">
  <div style="text-align:center;margin-bottom:24px;">
    {LOGO_SVG}
    <div style="font-size:13px;font-weight:900;color:#1a6b3c;letter-spacing:0.25em;margin-top:8px;">FOREWISE</div>
  </div>
  <h1 style="text-align:center;font-size:22px;color:#1a2e21;margin-bottom:4px;">הזמנת עבודה #{wo.order_number or wo.id}</h1>
  <div style="text-align:center;margin-bottom:24px;">{status_badge}</div>
  <table style="width:100%;border-collapse:collapse;border:1px solid #dde8e2;border-radius:10px;overflow:hidden;">
    {table_rows}
  </table>
  <div class="no-print" style="text-align:center;margin-top:32px;">
    <button onclick="window.print()" style="background:#1a6b3c;color:#fff;border:none;padding:12px 32px;border-radius:8px;font-size:16px;cursor:pointer;font-family:inherit;"> הדפס / שמור כ-PDF</button>
  </div>
  <div style="text-align:center;margin-top:24px;font-size:11px;color:#aab8b2;">
    Forewise — מערכת ניהול יערות &bull; הופק בתאריך {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}
  </div>
</div>
</body>
</html>"""


@router.get("/{work_order_id}/pdf")
def get_work_order_pdf(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Generate and return Work Order PDF (A4, RTL, weasyprint)."""
    require_permission(current_user, "work_orders.read")

    from fastapi.responses import Response
    from app.services.pdf_documents import generate_work_order_pdf

    try:
        pdf_bytes = generate_work_order_pdf(work_order_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Work Order PDF generation failed: {e}")
        from fastapi.responses import HTMLResponse
        html = _build_work_order_html(
            db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first(), db
        )
        return HTMLResponse(content=html)

    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    filename = f"work_order_{wo.order_number or work_order_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
