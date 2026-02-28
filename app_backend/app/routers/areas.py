"""
Areas Router
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.area import (
    AreaCreate, AreaUpdate, AreaResponse,
    AreaList, AreaSearch, AreaStatistics
)
from app.services.area_service import AreaService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

router = APIRouter(prefix="/areas", tags=["Areas"])
area_service = AreaService()


@router.get("", response_model=AreaList)
def list_areas(
    search: Annotated[AreaSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List areas"""
    require_permission(current_user, "areas.read")
    areas, total = area_service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return AreaList(items=areas, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


@router.get("/statistics", response_model=AreaStatistics)
def get_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get statistics"""
    require_permission(current_user, "areas.read")
    return area_service.get_statistics(db)


@router.get("/by-code/{code}", response_model=AreaResponse)
def get_by_code(
    code: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get by code"""
    require_permission(current_user, "areas.read")
    area = area_service.get_by_code(db, code)
    if not area:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Area '{code}' not found")
    return area


@router.get("/{area_id}", response_model=AreaResponse)
def get_area(
    area_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get area"""
    require_permission(current_user, "areas.read")
    area = area_service.get_by_id_or_404(db, area_id)
    return area


@router.post("", response_model=AreaResponse, status_code=status.HTTP_201_CREATED)
def create_area(
    data: AreaCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create area"""
    require_permission(current_user, "areas.create")
    try:
        area = area_service.create(db, data, current_user.id)
        return area
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{area_id}", response_model=AreaResponse)
def update_area(
    area_id: int,
    data: AreaUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update area"""
    require_permission(current_user, "areas.update")
    try:
        area = area_service.update(db, area_id, data, current_user.id)
        return area
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_area(
    area_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Delete area"""
    require_permission(current_user, "areas.delete")
    try:
        area_service.soft_delete(db, area_id, current_user.id)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{area_id}/restore", response_model=AreaResponse)
def restore_area(
    area_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Restore area"""
    require_permission(current_user, "areas.restore")
    area = area_service.restore(db, area_id, current_user.id)
    return area
