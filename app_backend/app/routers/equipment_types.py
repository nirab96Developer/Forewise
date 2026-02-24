"""
Equipment Types Router
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.equipment_type import (
    EquipmentTypeCreate, EquipmentTypeUpdate, EquipmentTypeResponse,
    EquipmentTypeList, EquipmentTypeSearch, EquipmentTypeStatistics
)
from app.services.equipment_type_service import EquipmentTypeService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

router = APIRouter(prefix="/equipment-types", tags=["Equipment Types"])
eq_type_service = EquipmentTypeService()


@router.get("", response_model=EquipmentTypeList)
def list_equipment_types(
    search: Annotated[EquipmentTypeSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List equipment types"""
    require_permission(current_user, "equipment_types.read")
    items, total = eq_type_service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return EquipmentTypeList(items=items, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


@router.get("/statistics", response_model=EquipmentTypeStatistics)
def get_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get statistics"""
    require_permission(current_user, "equipment_types.read")
    return eq_type_service.get_statistics(db)


@router.get("/by-code/{code}", response_model=EquipmentTypeResponse)
def get_by_code(
    code: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get by code"""
    require_permission(current_user, "equipment_types.read")
    item = eq_type_service.get_by_code(db, code)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment type '{code}' not found")
    return item


@router.get("/{item_id}", response_model=EquipmentTypeResponse)
def get_equipment_type(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get equipment type"""
    require_permission(current_user, "equipment_types.read")
    item = eq_type_service.get_by_id_or_404(db, item_id)
    return item


@router.post("", response_model=EquipmentTypeResponse, status_code=status.HTTP_201_CREATED)
def create_equipment_type(
    data: EquipmentTypeCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create equipment type"""
    require_permission(current_user, "equipment_types.create")
    try:
        item = eq_type_service.create(db, data, current_user.id)
        return item
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{item_id}", response_model=EquipmentTypeResponse)
def update_equipment_type(
    item_id: int,
    data: EquipmentTypeUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update equipment type"""
    require_permission(current_user, "equipment_types.update")
    try:
        item = eq_type_service.update(db, item_id, data, current_user.id)
        return item
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_equipment_type(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Deactivate equipment type"""
    require_permission(current_user, "equipment_types.delete")
    try:
        eq_type_service.deactivate(db, item_id, current_user.id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{item_id}/activate", response_model=EquipmentTypeResponse)
def activate_equipment_type(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Activate equipment type"""
    require_permission(current_user, "equipment_types.restore")
    item = eq_type_service.activate(db, item_id, current_user.id)
    return item
