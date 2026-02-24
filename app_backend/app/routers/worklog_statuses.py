# app/routers/worklog_statuses.py
"""Worklog status management endpoints."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.worklog_status import WorklogStatus

router = APIRouter(prefix="/worklog-statuses", tags=["Worklog Statuses"])


@router.get("/", response_model=List[dict])
def get_worklog_statuses(
    db: Session = Depends(get_db),
    is_active: Optional[bool] = Query(None),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(require_permission("worklogs.read")),
):
    """Get list of worklog statuses."""
    query = db.query(WorklogStatus)
    
    if is_active is not None:
        query = query.filter(WorklogStatus.is_active == is_active)
    
    statuses = query.order_by(WorklogStatus.display_order, WorklogStatus.code).all()
    
    return [
        {
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "description": s.description,
            "is_active": s.is_active,
            "display_order": s.display_order,
        }
        for s in statuses
    ]


@router.get("/{status_id}", response_model=dict)
def get_worklog_status(
    status_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(require_permission("worklogs.read")),
):
    """Get a specific worklog status."""
    status_obj = db.query(WorklogStatus).filter(WorklogStatus.id == status_id).first()
    
    if not status_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worklog status not found"
        )
    
    return {
        "id": status_obj.id,
        "code": status_obj.code,
        "name": status_obj.name,
        "description": status_obj.description,
        "is_active": status_obj.is_active,
        "display_order": status_obj.display_order,
    }
