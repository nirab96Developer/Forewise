"""
Supplier Constraint Reasons Router
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.supplier_constraint_reason import (
    SupplierConstraintReasonCreate, SupplierConstraintReasonUpdate, SupplierConstraintReasonResponse,
    SupplierConstraintReasonList, SupplierConstraintReasonSearch, SupplierConstraintReasonStatistics
)
from app.services.supplier_constraint_reason_service import SupplierConstraintReasonService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

router = APIRouter(prefix="/supplier-constraint-reasons", tags=["Supplier Constraint Reasons"])
service = SupplierConstraintReasonService()


@router.get("", response_model=SupplierConstraintReasonList)
def list_reasons(
    search: Annotated[SupplierConstraintReasonSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List supplier constraint reasons"""
    require_permission(current_user, "supplier_constraint_reasons.read")
    items, total = service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return SupplierConstraintReasonList(items=items, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


@router.get("/statistics", response_model=SupplierConstraintReasonStatistics)
def get_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get statistics"""
    require_permission(current_user, "supplier_constraint_reasons.read")
    return service.get_statistics(db)


@router.get("/by-code/{code}", response_model=SupplierConstraintReasonResponse)
def get_by_code(
    code: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get by code"""
    require_permission(current_user, "supplier_constraint_reasons.read")
    item = service.get_by_code(db, code)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reason '{code}' not found")
    return item


@router.get("/{item_id}", response_model=SupplierConstraintReasonResponse)
def get_reason(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get supplier constraint reason"""
    require_permission(current_user, "supplier_constraint_reasons.read")
    item = service.get_by_id_or_404(db, item_id)
    return item


@router.post("", response_model=SupplierConstraintReasonResponse, status_code=status.HTTP_201_CREATED)
def create_reason(
    data: SupplierConstraintReasonCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create supplier constraint reason"""
    require_permission(current_user, "supplier_constraint_reasons.create")
    try:
        item = service.create(db, data, current_user.id)
        return item
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{item_id}", response_model=SupplierConstraintReasonResponse)
def update_reason(
    item_id: int,
    data: SupplierConstraintReasonUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update supplier constraint reason"""
    require_permission(current_user, "supplier_constraint_reasons.update")
    try:
        item = service.update(db, item_id, data, current_user.id)
        return item
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# PATCH alias — same handler, semantically more correct for partial updates
# (e.g. the FE "toggle is_active" button which only sends one field).
@router.patch("/{item_id}", response_model=SupplierConstraintReasonResponse)
def patch_reason(
    item_id: int,
    data: SupplierConstraintReasonUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Partially update a supplier constraint reason (alias of PUT)."""
    return update_reason(item_id, data, db, current_user)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reason(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Soft delete supplier constraint reason"""
    require_permission(current_user, "supplier_constraint_reasons.delete")
    try:
        service.soft_delete(db, item_id, current_user.id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{item_id}/restore", response_model=SupplierConstraintReasonResponse)
def restore_reason(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Restore supplier constraint reason"""
    require_permission(current_user, "supplier_constraint_reasons.restore")
    item = service.restore(db, item_id, current_user.id)
    return item
