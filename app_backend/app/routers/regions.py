"""
Regions Router
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.region import (
    RegionCreate, RegionUpdate, RegionResponse,
    RegionList, RegionSearch, RegionStatistics
)
from app.services.region_service import RegionService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

router = APIRouter(prefix="/regions", tags=["Regions"])
region_service = RegionService()


@router.get("", response_model=RegionList)
def list_regions(
    search: Annotated[RegionSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List regions"""
    require_permission(current_user, "regions.read")
    regions, total = region_service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return RegionList(items=regions, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


@router.get("/statistics", response_model=RegionStatistics)
def get_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get statistics"""
    require_permission(current_user, "regions.read")
    return region_service.get_statistics(db)


@router.get("/by-code/{code}", response_model=RegionResponse)
def get_by_code(
    code: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get by code"""
    require_permission(current_user, "regions.read")
    region = region_service.get_by_code(db, code)
    if not region:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Region '{code}' not found")
    return region


@router.get("/{region_id}", response_model=RegionResponse)
def get_region(
    region_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get region"""
    require_permission(current_user, "regions.read")
    region = region_service.get_by_id_or_404(db, region_id)
    return region


@router.post("", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
def create_region(
    data: RegionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create region"""
    require_permission(current_user, "regions.create")
    try:
        region = region_service.create(db, data, current_user.id)
        return region
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{region_id}", response_model=RegionResponse)
def update_region(
    region_id: int,
    data: RegionUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update region"""
    require_permission(current_user, "regions.update")
    try:
        region = region_service.update(db, region_id, data, current_user.id)
        return region
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{region_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_region(
    region_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Delete region"""
    require_permission(current_user, "regions.delete")
    try:
        region_service.soft_delete(db, region_id, current_user.id)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{region_id}/restore", response_model=RegionResponse)
def restore_region(
    region_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Restore region"""
    require_permission(current_user, "regions.restore")
    region = region_service.restore(db, region_id, current_user.id)
    return region
