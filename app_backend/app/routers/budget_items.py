"""
BudgetItems Router
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.budget_item import (
    BudgetItemCreate, BudgetItemUpdate, BudgetItemResponse,
    BudgetItemList, BudgetItemSearch, BudgetItemStatistics
)
from app.services.budget_item_service import BudgetItemService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

router = APIRouter(prefix="/budget-items", tags=["Budget Items"])
budget_item_service = BudgetItemService()


@router.get("", response_model=BudgetItemList)
def list_budget_items(
    search: Annotated[BudgetItemSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List budget items"""
    require_permission(current_user, "budget_items.read")
    items, total = budget_item_service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return BudgetItemList(items=items, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


@router.get("/{item_id}", response_model=BudgetItemResponse)
def get_budget_item(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get budget item"""
    require_permission(current_user, "budget_items.read")
    item = budget_item_service.get_by_id_or_404(db, item_id)
    return item


@router.post("", response_model=BudgetItemResponse, status_code=status.HTTP_201_CREATED)
def create_budget_item(
    data: BudgetItemCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create budget item"""
    require_permission(current_user, "budget_items.create")
    try:
        item = budget_item_service.create(db, data, current_user.id)
        return item
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{item_id}", response_model=BudgetItemResponse)
def update_budget_item(
    item_id: int,
    data: BudgetItemUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update budget item"""
    require_permission(current_user, "budget_items.update")
    try:
        item = budget_item_service.update(db, item_id, data, current_user.id)
        return item
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget_item(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Delete budget item"""
    require_permission(current_user, "budget_items.delete")
    try:
        budget_item_service.soft_delete(db, item_id, current_user.id)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{item_id}/restore", response_model=BudgetItemResponse)
def restore_budget_item(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Restore budget item"""
    require_permission(current_user, "budget_items.restore")
    item = budget_item_service.restore(db, item_id, current_user.id)
    return item


@router.get("/statistics", response_model=BudgetItemStatistics)
def get_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    budget_id: Optional[int] = Query(None, description="Filter by budget")
):
    """Get statistics"""
    require_permission(current_user, "budget_items.read")
    return budget_item_service.get_statistics(db, budget_id)
