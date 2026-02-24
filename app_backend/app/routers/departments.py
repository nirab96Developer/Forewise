"""
Departments Router
"""

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.department import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    DepartmentList, DepartmentSearch, DepartmentStatistics, DepartmentBrief
)
from app.services.department_service import DepartmentService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

router = APIRouter(prefix="/departments", tags=["Departments"])
dept_service = DepartmentService()


@router.get("", response_model=DepartmentList)
def list_departments(
    search: Annotated[DepartmentSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List departments"""
    require_permission(current_user, "departments.read")
    depts, total = dept_service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return DepartmentList(items=depts, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


@router.get("/statistics", response_model=DepartmentStatistics)
def get_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get statistics"""
    require_permission(current_user, "departments.read")
    return dept_service.get_statistics(db)


@router.get("/by-code/{code}", response_model=DepartmentResponse)
def get_by_code(
    code: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get by code"""
    require_permission(current_user, "departments.read")
    dept = dept_service.get_by_code(db, code)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Department '{code}' not found")
    return dept


@router.get("/{dept_id}", response_model=DepartmentResponse)
def get_department(
    dept_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get department"""
    require_permission(current_user, "departments.read")
    dept = dept_service.get_by_id_or_404(db, dept_id)
    return dept


@router.get("/{dept_id}/children", response_model=List[DepartmentBrief])
def get_children(
    dept_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get child departments"""
    require_permission(current_user, "departments.read")
    return dept_service.get_children(db, dept_id)


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create department"""
    require_permission(current_user, "departments.create")
    try:
        dept = dept_service.create(db, data, current_user.id)
        return dept
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{dept_id}", response_model=DepartmentResponse)
def update_department(
    dept_id: int,
    data: DepartmentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update department"""
    require_permission(current_user, "departments.update")
    try:
        dept = dept_service.update(db, dept_id, data, current_user.id)
        return dept
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    dept_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Delete department"""
    require_permission(current_user, "departments.delete")
    try:
        dept_service.soft_delete(db, dept_id, current_user.id)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{dept_id}/restore", response_model=DepartmentResponse)
def restore_department(
    dept_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Restore department"""
    require_permission(current_user, "departments.restore")
    dept = dept_service.restore(db, dept_id, current_user.id)
    return dept
