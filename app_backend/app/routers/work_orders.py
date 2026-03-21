"""
WorkOrders Router - API endpoints להזמנות עבודה
Handles HTTP requests with state machine support
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.models.work_order import WorkOrder
from app.models.project import Project
from app.services.notification_service import (
    notify_work_order_created,
    notify_work_order_approved,
    notify_work_order_rejected,
)
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderResponse,
    WorkOrderBrief,
    WorkOrderList,
    WorkOrderSearch,
    WorkOrderStatusUpdate,
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


def _to_response(work_order, db: Session) -> dict:
    """Serialize WorkOrder ORM object + inject computed hours."""
    from pydantic import TypeAdapter
    d = WorkOrderResponse.model_validate(work_order).model_dump()
    d.update(_enrich_hours(work_order, db))
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
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list work orders: {str(e)}"
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

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
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

        if current_user.area_id is not None:
            query = query.where(Project.area_id == current_user.area_id)

        work_order = db.execute(query).scalar_one_or_none()
        if not work_order:
            raise NotFoundException("WorkOrder not found")

        return _to_response(work_order, db)

    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get work order: {str(e)}"
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
        return work_order
    
    except HTTPException:
        raise  # pass-through 400/422/404 etc from service layer
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create work order: {str(e)}"
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update work order: {str(e)}"
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
                VALUES ('WORK_ORDER_DELETED', 'delete', 'work_order', :entity_id, :user_id, :description)
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete work order: {str(e)}"
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore work order: {str(e)}"
        )


@router.post("/{work_order_id}/approve", response_model=WorkOrderResponse)
def approve_work_order(
    work_order_id: int,
    request: WorkOrderApproveRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Approve work order
    
    Business Rule: equipment_id is REQUIRED for approval!
    
    Permissions: work_orders.approve
    """
    require_permission(current_user, "work_orders.approve")
    
    try:
        work_order = work_order_service.approve(db, work_order_id, request, current_user_id=current_user.id)
        notify_work_order_approved(db, work_order)
        
        # Send Email 4 — work order approved to all stakeholders
        try:
            from app.templates.email_worklog import work_order_approved
            from app.core.email import send_email
            from sqlalchemy import text as sa_text
            
            project = work_order.project
            supplier = work_order.supplier
            eq = db.execute(sa_text("SELECT equipment_type, license_plate FROM equipment WHERE id=:eid"),
                           {"eid": work_order.equipment_id}).first() if work_order.equipment_id else None
            
            common = dict(
                order_number=work_order.order_number or work_order.id,
                project_name=project.name if project else '',
                project_code=project.code if project else '',
                supplier_name=supplier.name if supplier else '',
                equipment_type=eq[0] if eq else (work_order.equipment_type or ''),
                license_plate=eq[1] if eq else '',
                work_start=str(work_order.work_start_date or ''),
                work_end=str(work_order.work_end_date or ''),
                estimated_hours=work_order.estimated_hours or 0,
                area_name=getattr(project, 'area', None) and project.area.name if project else '',
                region_name=getattr(project, 'region', None) and project.region.name if project else '',
                worker_name=current_user.full_name or current_user.username or '',
            )
            
            recipients = db.execute(sa_text("""
                SELECT DISTINCT u.email, r.code FROM users u JOIN roles r ON u.role_id=r.id
                WHERE r.code IN ('ORDER_COORDINATOR','ADMIN','AREA_MANAGER','WORK_MANAGER')
                AND u.is_active=true AND u.email IS NOT NULL
            """)).fetchall()
            
            role_labels = {'ORDER_COORDINATOR':'עותק למתאם הזמנות','ADMIN':'עותק למנהל מערכת',
                          'AREA_MANAGER':'עותק למנהל אזור','WORK_MANAGER':'עותק למנהל עבודה'}
            
            for row in recipients:
                tmpl = work_order_approved(**common, recipient_label=role_labels.get(row[1],''))
                send_email(to=row[0], subject=tmpl["subject"], body="", html_body=tmpl["html"])
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Email 4 (WO approved) failed: {e}")
        
        return work_order
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve work order: {str(e)}"
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject work order: {str(e)}"
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel work order: {str(e)}"
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close work order: {str(e)}"
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
    return approve_work_order(work_order_id, request, db, current_user)


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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start work order: {str(e)}"
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send to supplier: {str(e)}"
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
    
    try:
        work_order = work_order_service.move_to_next_supplier(db, work_order_id, current_user.id)
        return work_order
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move to next supplier: {str(e)}"
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
    
    try:
        work_order = work_order_service.resend_to_supplier(db, work_order_id, current_user.id)
        return work_order
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend to supplier: {str(e)}"
        )


@router.post("/{work_order_id}/remove-equipment", response_model=WorkOrderResponse)
def remove_equipment_from_project(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Remove equipment from project — release budget, free equipment."""
    require_permission(current_user, "work_orders.update")
    
    try:
        from app.services.budget_service import release_budget_freeze
        from sqlalchemy import text as sa_text
        
        work_order = work_order_service.get_work_order(db, work_order_id)
        if not work_order:
            raise HTTPException(status_code=404, detail="הזמנה לא נמצאה")
        
        # Release remaining frozen budget
        released = 0
        if getattr(work_order, 'remaining_frozen', 0) and work_order.remaining_frozen > 0:
            released = float(work_order.remaining_frozen)
            try:
                release_budget_freeze(work_order_id, 0, db)
            except Exception:
                pass
        
        # Update status
        work_order.status = 'STOPPED'
        work_order.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(work_order)
        
        # Notify
        try:
            from app.services.notification_service import notify
            from sqlalchemy import text
            coordinators = db.execute(text("""
                SELECT u.id FROM users u JOIN roles r ON u.role_id=r.id
                WHERE r.code IN ('ORDER_COORDINATOR','ADMIN','ACCOUNTANT') AND u.is_active=true
            """)).fetchall()
            wo_num = work_order.order_number or work_order.id
            for row in coordinators:
                notify(db, row[0],
                    title=f"כלי הוסר מפרויקט — הזמנה #{wo_num}",
                    message=f"יתרה תקציבית ₪{released:,.0f} שוחררה",
                    notification_type="work_order",
                    entity_type="work_order",
                    entity_id=work_order.id,
                    priority="medium",
                )
        except Exception:
            pass
        
        return work_order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"שגיאה בהסרת כלי: {str(e)}")
