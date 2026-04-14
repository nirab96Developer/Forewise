"""
Reports Router
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.report import (
    ReportCreate, ReportUpdate, ReportSearch, ReportStatistics
)
from app.services.report_service import ReportService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

router = APIRouter(prefix="/reports", tags=["Reports"])
report_service = ReportService()


@router.get("", )
def list_reports(
    search: Annotated[ReportSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List reports"""
    require_permission(current_user, "reports.read")
    reports, total = report_service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return {"items": reports, "total": total, "page": search.page, "page_size": search.page_size, "total_pages": total_pages}


@router.get("/statistics", response_model=ReportStatistics)
def get_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get statistics"""
    require_permission(current_user, "reports.read")
    return report_service.get_statistics(db)


@router.get("/by-code/{code}", )
def get_by_code(
    code: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get by code"""
    require_permission(current_user, "reports.read")
    report = report_service.get_by_code(db, code)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report '{code}' not found")
    return report


@router.get("/{report_id}", )
def get_report(
    report_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get report"""
    require_permission(current_user, "reports.read")
    report = report_service.get_by_id_or_404(db, report_id)
    return report


@router.post("", status_code=status.HTTP_201_CREATED)
def create_report(
    data: ReportCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create report"""
    require_permission(current_user, "reports.create")
    try:
        report = report_service.create(db, data, current_user.id)
        return report
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{report_id}", )
def update_report(
    report_id: int,
    data: ReportUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update report"""
    require_permission(current_user, "reports.update")
    try:
        report = report_service.update(db, report_id, data, current_user.id)
        return report
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Delete report"""
    require_permission(current_user, "reports.delete")
    try:
        report_service.soft_delete(db, report_id, current_user.id)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{report_id}/restore", )
def restore_report(
    report_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Restore report"""
    require_permission(current_user, "reports.restore")
    report = report_service.restore(db, report_id, current_user.id)
    return report
