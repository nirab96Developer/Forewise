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
        
        return WorkOrderList(
            items=work_orders,
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

        return work_order

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
    Delete work order (soft delete)
    
    Permissions: work_orders.delete
    """
    require_permission(current_user, "work_orders.delete")
    
    try:
        work_order_service.soft_delete(db, work_order_id, current_user_id=current_user.id)
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
    """
    require_permission(current_user, "work_orders.update")

    try:
        result = work_order_service.send_to_supplier(db, work_order_id, current_user.id)
        wo = result["work_order"]
        return {
            "portal_token": result["portal_token"],
            "portal_url": result["portal_url"],
            "expires_at": result["expires_at"],
            "work_order_id": wo.id,
            "status": wo.status,
            "message": f"ההזמנה נשלחה לספק. הקישור תקף ל-3 שעות.",
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
