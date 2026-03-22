"""
Budget Transfers Router — בקשות העברת תקציב
POST /api/v1/budget-transfers/request
POST /api/v1/budget-transfers/{id}/approve
POST /api/v1/budget-transfers/{id}/reject
GET  /api/v1/budget-transfers
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.models.budget_transfer import BudgetTransfer
from app.services.budget_service import (
    request_budget_transfer,
    approve_budget_transfer,
    reject_budget_transfer,
)

router = APIRouter(prefix="/budget-transfers", tags=["budget-transfers"])


class TransferRequest(BaseModel):
    from_budget_id: int
    to_budget_id: int
    amount: float
    reason: str
    transfer_type: str = "regular"


class ApproveRequest(BaseModel):
    approved_amount: float
    notes: str = ""


class RejectRequest(BaseModel):
    reason: str


def _serialize(t: BudgetTransfer) -> dict:
    return {
        "id": t.id,
        "from_budget_id": t.from_budget_id,
        "to_budget_id": t.to_budget_id,
        "requested_by": t.requested_by,
        "approved_by": t.approved_by,
        "amount": float(t.amount or 0),
        "transfer_type": t.transfer_type,
        "reason": t.reason,
        "status": t.status,
        "notes": t.notes,
        "rejected_reason": t.rejected_reason,
        "requested_at": t.requested_at.isoformat() if t.requested_at else None,
        "approved_at": t.approved_at.isoformat() if t.approved_at else None,
        "executed_at": t.executed_at.isoformat() if t.executed_at else None,
    }


@router.post("/request", status_code=status.HTTP_201_CREATED)
def create_transfer_request(
    body: TransferRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """מנהל אזור / מרחב מבקש העברת תקציב"""
    require_permission(current_user, "budgets.view")
    try:
        transfer = request_budget_transfer(
            from_budget_id=body.from_budget_id,
            to_budget_id=body.to_budget_id,
            amount=body.amount,
            reason=body.reason,
            requested_by=current_user.id,
            transfer_type=body.transfer_type,
            db=db,
        )
        return _serialize(transfer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{transfer_id}/approve")
def approve_transfer(
    transfer_id: int,
    body: ApproveRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """מנהל מרחב מאשר (מלא / חלקי)"""
    require_permission(current_user, "budgets.edit")
    try:
        transfer = approve_budget_transfer(
            transfer_id=transfer_id,
            approved_by=current_user.id,
            approved_amount=body.approved_amount,
            notes=body.notes,
            db=db,
        )
        return _serialize(transfer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{transfer_id}/reject")
def reject_transfer(
    transfer_id: int,
    body: RejectRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """מנהל מרחב דוחה בקשה"""
    require_permission(current_user, "budgets.edit")
    try:
        transfer = reject_budget_transfer(
            transfer_id=transfer_id,
            rejected_by=current_user.id,
            reason=body.reason,
            db=db,
        )
        return _serialize(transfer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def list_transfers(
    region_id: Optional[int] = None,
    area_id: Optional[int] = None,
    budget_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """רשימת בקשות העברה — סינון לפי מרחב / אזור / תקציב / סטטוס"""
    require_permission(current_user, "budgets.view")

    q = db.query(BudgetTransfer)

    if budget_id:
        q = q.filter(
            (BudgetTransfer.from_budget_id == budget_id) |
            (BudgetTransfer.to_budget_id == budget_id)
        )
    if status_filter:
        q = q.filter(BudgetTransfer.status == status_filter.upper())

    # סינון לפי אזור/מרחב — דרך טבלת budgets
    if area_id or region_id:
        from app.models.budget import Budget
        budget_ids_q = db.query(Budget.id)
        if area_id:
            budget_ids_q = budget_ids_q.filter(Budget.area_id == area_id)
        elif region_id:
            budget_ids_q = budget_ids_q.filter(Budget.region_id == region_id)
        budget_ids = [b.id for b in budget_ids_q.all()]
        q = q.filter(
            (BudgetTransfer.from_budget_id.in_(budget_ids)) |
            (BudgetTransfer.to_budget_id.in_(budget_ids))
        )

    transfers = q.order_by(BudgetTransfer.created_at.desc()).all()
    return [_serialize(t) for t in transfers]
