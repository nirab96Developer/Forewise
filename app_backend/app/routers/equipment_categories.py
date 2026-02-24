"""
Equipment Categories Router
"""

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.equipment_category import (
    EquipmentCategoryCreate, EquipmentCategoryUpdate, EquipmentCategoryResponse,
    EquipmentCategoryList, EquipmentCategorySearch, EquipmentCategoryStatistics, EquipmentCategoryBrief
)
from app.services.equipment_category_service import EquipmentCategoryService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

router = APIRouter(prefix="/equipment-categories", tags=["Equipment Categories"])
service = EquipmentCategoryService()


@router.get("", response_model=EquipmentCategoryList)
def list_categories(
    search: Annotated[EquipmentCategorySearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List equipment categories"""
    require_permission(current_user, "equipment_categories.read")
    items, total = service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return EquipmentCategoryList(items=items, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


@router.get("/statistics", response_model=EquipmentCategoryStatistics)
def get_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get statistics"""
    require_permission(current_user, "equipment_categories.read")
    return service.get_statistics(db)


@router.get("/by-code/{code}", response_model=EquipmentCategoryResponse)
def get_by_code(
    code: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get by code"""
    require_permission(current_user, "equipment_categories.read")
    item = service.get_by_code(db, code)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category '{code}' not found")
    return item


@router.get("/{item_id}", response_model=EquipmentCategoryResponse)
def get_category(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get equipment category"""
    require_permission(current_user, "equipment_categories.read")
    item = service.get_by_id_or_404(db, item_id)
    return item


@router.get("/{item_id}/children", response_model=List[EquipmentCategoryBrief])
def get_children(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get child categories"""
    require_permission(current_user, "equipment_categories.read")
    return service.get_children(db, item_id)


@router.post("", response_model=EquipmentCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: EquipmentCategoryCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create equipment category"""
    require_permission(current_user, "equipment_categories.create")
    try:
        item = service.create(db, data, current_user.id)
        return item
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{item_id}", response_model=EquipmentCategoryResponse)
def update_category(
    item_id: int,
    data: EquipmentCategoryUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update equipment category"""
    require_permission(current_user, "equipment_categories.update")
    try:
        item = service.update(db, item_id, data, current_user.id)
        return item
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Soft delete equipment category"""
    require_permission(current_user, "equipment_categories.delete")
    try:
        service.soft_delete(db, item_id, current_user.id)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{item_id}/restore", response_model=EquipmentCategoryResponse)
def restore_category(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Restore equipment category"""
    require_permission(current_user, "equipment_categories.restore")
    item = service.restore(db, item_id, current_user.id)
    return item
