"""
Work Order Coordination Logs Router
API endpoint for logging coordination actions (calls, notes, etc.)
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.work_order import WorkOrder
from app.models.work_order_coordination_log import WorkOrderCoordinationLog

router = APIRouter(prefix="/work-order-coordination-logs", tags=["Work Order Coordination Logs"])


class CoordinationLogCreate(BaseModel):
    work_order_id: int
    action_type: str = Field(..., max_length=50)
    note: Optional[str] = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_coordination_log(
    data: CoordinationLogCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Create a coordination log entry for a work order."""
    wo = db.query(WorkOrder).filter(
        WorkOrder.id == data.work_order_id,
        WorkOrder.deleted_at.is_(None),
    ).first()
    if not wo:
        raise HTTPException(status_code=404, detail="הזמנת עבודה לא נמצאה")

    log = WorkOrderCoordinationLog(
        work_order_id=data.work_order_id,
        created_by_user_id=current_user.id,
        action_type=data.action_type,
        note=data.note,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        "id": log.id,
        "work_order_id": log.work_order_id,
        "action_type": log.action_type,
        "note": log.note,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }
