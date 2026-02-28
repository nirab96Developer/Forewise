"""
ReportRuns Router
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.report_run import (
    ReportRunCreate, ReportRunUpdate, ReportRunResponse,
    ReportRunList, ReportRunSearch, ReportRunStatistics
)
from app.services.report_run_service import ReportRunService
from app.core.exceptions import NotFoundException, ValidationException

router = APIRouter(prefix="/report-runs", tags=["Report Runs"])
report_run_service = ReportRunService()


@router.get("", response_model=ReportRunList)
def list_report_runs(
    search: Annotated[ReportRunSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List report runs"""
    require_permission(current_user, "report_runs.read")
    runs, total = report_run_service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return ReportRunList(items=runs, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


@router.get("/statistics", response_model=ReportRunStatistics)
def get_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    report_id: Optional[int] = Query(None)
):
    """Get statistics"""
    require_permission(current_user, "report_runs.read")
    return report_run_service.get_statistics(db, report_id)


@router.get("/{run_id}", response_model=ReportRunResponse)
def get_report_run(
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get report run"""
    require_permission(current_user, "report_runs.read")
    run = report_run_service.get_by_id(db, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


@router.post("", response_model=ReportRunResponse, status_code=status.HTTP_201_CREATED)
def create_report_run(
    data: ReportRunCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create report run"""
    require_permission(current_user, "report_runs.create")
    try:
        run = report_run_service.create(db, data, current_user.id)
        return run
    except (ValidationException,) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{run_id}", response_model=ReportRunResponse)
def update_report_run(
    run_id: int,
    data: ReportRunUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update report run"""
    require_permission(current_user, "report_runs.update")
    try:
        run = report_run_service.update(db, run_id, data, current_user.id)
        return run
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
