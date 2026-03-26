"""
Budget Service
"""

from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_

from app.models.budget import Budget
from app.models.budget_item import BudgetItem
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetSearch, BudgetStatistics
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException


class BudgetService(BaseService[Budget]):
    """Budget Service - CORE"""
    
    def __init__(self):
        super().__init__(Budget)

    def _base_query(self, db: Session, include_deleted: bool = False):
        """Override to eagerly load related objects and avoid N+1."""
        query = select(Budget).options(
            selectinload(Budget.items),
            selectinload(Budget.created_by_user),
        )
        if not include_deleted:
            query = query.where(Budget.deleted_at.is_(None))
        return query

    def create(self, db: Session, data: BudgetCreate, current_user_id: int) -> Budget:
        """Create budget"""
        # UNIQUE: code
        if data.code:
            existing = db.query(Budget).filter(
                Budget.code == data.code,
                Budget.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Budget with code '{data.code}' already exists")
        
        # Validate parent_budget_id
        if data.parent_budget_id:
            parent = db.query(Budget).filter_by(id=data.parent_budget_id).first()
            if not parent:
                raise ValidationException(f"Parent budget {data.parent_budget_id} not found")
        
        # Create
        budget_dict = data.model_dump(exclude_unset=True)
        budget_dict['created_by'] = current_user_id
        budget = Budget(**budget_dict)
        
        db.add(budget)
        db.commit()
        db.refresh(budget)
        return budget
    
    def update(self, db: Session, budget_id: int, data: BudgetUpdate, current_user_id: int) -> Budget:
        """Update budget"""
        budget = self.get_by_id_or_404(db, budget_id)
        
        # Version check
        if data.version is not None and budget.version != data.version:
            raise DuplicateException("Budget was modified by another user")
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        # UNIQUE: code
        if 'code' in update_dict and update_dict['code'] and update_dict['code'] != budget.code:
            existing = db.query(Budget).filter(
                Budget.code == update_dict['code'],
                Budget.id != budget_id,
                Budget.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Budget with code '{update_dict['code']}' already exists")
        
        # Update
        for field, value in update_dict.items():
            setattr(budget, field, value)
        
        if budget.version is not None:
            budget.version += 1
        
        db.commit()
        db.refresh(budget)
        return budget
    
    def list(self, db: Session, search: BudgetSearch) -> Tuple[List[Budget], int]:
        """List budgets"""
        query = self._base_query(db, include_deleted=search.include_deleted)
        
        if search.q:
            term = f"%{search.q}%"
            query = query.where(or_(Budget.name.ilike(term), Budget.code.ilike(term)))
        
        if search.budget_type:
            query = query.where(Budget.budget_type == search.budget_type)
        if search.status:
            query = query.where(Budget.status == search.status)
        if search.parent_budget_id:
            query = query.where(Budget.parent_budget_id == search.parent_budget_id)
        if search.fiscal_year:
            query = query.where(Budget.fiscal_year == search.fiscal_year)
        if search.is_active is not None:
            query = query.where(Budget.is_active == search.is_active)
        
        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        
        sort_col = getattr(Budget, search.sort_by, Budget.name)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        offset = (search.page - 1) * search.page_size
        budgets = db.execute(query.offset(offset).limit(search.page_size)).scalars().all()
        
        return budgets, total
    
    def soft_delete(self, db: Session, budget_id: int, current_user_id: int) -> Budget:
        """Soft delete budget"""
        budget = self.get_by_id_or_404(db, budget_id)
        
        # Check no active items
        active_items = db.query(BudgetItem).filter(
            BudgetItem.budget_id == budget_id,
            BudgetItem.is_active == True,
            BudgetItem.deleted_at.is_(None)
        ).count()
        
        if active_items > 0:
            raise ValidationException(f"Cannot delete budget with {active_items} active items")
        
        return super().soft_delete(db, budget_id, commit=True)
    
    def get_by_code(self, db: Session, code: str) -> Optional[Budget]:
        """Get by code"""
        return db.execute(
            select(Budget).where(Budget.code == code, Budget.deleted_at.is_(None))
        ).scalar_one_or_none()
    
    def get_statistics(self, db: Session, filters: Optional[dict] = None) -> BudgetStatistics:
        """Get statistics"""
        query = select(Budget).where(Budget.deleted_at.is_(None))
        budgets = db.execute(query).scalars().all()
        
        return BudgetStatistics(
            total=len(budgets),
            total_amount=sum(b.total_amount for b in budgets),
            total_spent=sum(b.spent_amount or 0 for b in budgets),
            total_allocated=sum(b.allocated_amount or 0 for b in budgets),
            by_type={},
            by_status={}
        )


# ── Budget invariant helpers ──────────────────────────────────────────────────

import logging as _logging
_budget_log = _logging.getLogger("budget")


def _sync_remaining(budget) -> None:
    """Recompute remaining_amount from the canonical formula.

    INVARIANT: remaining = total - committed - spent (floored at 0)
    Called after every mutation to committed/spent/total.
    """
    from decimal import Decimal
    total = Decimal(str(budget.total_amount or 0))
    committed = Decimal(str(budget.committed_amount or 0))
    spent = Decimal(str(budget.spent_amount or 0))
    budget.remaining_amount = max(Decimal(0), total - committed - spent)


def _assert_invariants(budget, label: str = "") -> None:
    """Enforce budget financial invariants.

    In production (ENVIRONMENT=production): violations raise an exception.
    In development/testing: violations are logged as warnings.
    """
    from app.core.config import settings

    total = float(budget.total_amount or 0)
    committed = float(budget.committed_amount or 0)
    spent = float(budget.spent_amount or 0)
    remaining = float(budget.remaining_amount or 0)
    strict = settings.is_production()

    violations = []
    if committed < 0:
        violations.append(f"committed_amount < 0 ({committed})")
    if spent < 0:
        violations.append(f"spent_amount < 0 ({spent})")
    if remaining < 0:
        violations.append(f"remaining_amount < 0 ({remaining})")
    if total > 0 and (committed + spent) > total * 1.01:
        violations.append(f"committed+spent ({committed+spent:.0f}) exceeds total ({total:.0f})")

    if not violations:
        return

    msg = f"[{label}] budget #{budget.id}: " + "; ".join(violations)

    if strict:
        _budget_log.error(msg)
        from app.core.exceptions import BusinessException
        raise BusinessException(f"הפרת תקינות תקציבית: {'; '.join(violations)}")

    _budget_log.warning(msg)


# ── Freeze / Release / Transfer ────────────────────────────────────────────────

def freeze_budget_for_work_order(
    project_id: int,
    work_order_id: int,
    amount: float,
    db: "Session",
) -> None:
    """Freeze budget for a new work order. Raises ValueError if insufficient."""
    from app.models.budget import Budget
    from app.models.work_order import WorkOrder
    from decimal import Decimal

    budget = (
        db.query(Budget)
        .filter(Budget.project_id == project_id, Budget.is_active == True, Budget.deleted_at.is_(None))
        .first()
    )
    if not budget:
        raise ValueError("אין תקציב פעיל לפרויקט")

    total = float(budget.total_amount or 0)
    committed = float(budget.committed_amount or 0)
    spent = float(budget.spent_amount or 0)
    available = total - committed - spent

    if available < amount:
        raise ValueError(
            f"אין מספיק תקציב. זמין: ₪{available:,.0f}, נדרש: ₪{amount:,.0f}"
        )

    budget.committed_amount = Decimal(str(committed + amount))
    _sync_remaining(budget)
    _assert_invariants(budget, "freeze")

    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if wo:
        wo.frozen_amount = Decimal(str(amount))
        wo.remaining_frozen = Decimal(str(amount))

    from app.core.audit import log_business_event
    log_business_event(
        db, "BUDGET_FROZEN", "budget", budget.id,
        description=f"הוקפא ₪{amount:,.0f} עבור הזמנה #{work_order_id}",
        metadata={"work_order_id": work_order_id, "amount": amount,
                  "available_after": float(budget.remaining_amount or 0)},
        category="financial",
    )
    db.commit()


def release_budget_freeze(
    work_order_id: int,
    actual_amount: float,
    db: "Session",
) -> None:
    """Release frozen budget. actual_amount goes to spent; remainder returns to available."""
    from app.models.budget import Budget
    from app.models.work_order import WorkOrder
    from decimal import Decimal

    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo or not wo.project_id:
        return

    budget = (
        db.query(Budget)
        .filter(Budget.project_id == wo.project_id, Budget.is_active == True, Budget.deleted_at.is_(None))
        .first()
    )
    if not budget:
        return

    frozen = float(wo.frozen_amount or 0)
    budget.committed_amount = max(Decimal(0), (budget.committed_amount or Decimal(0)) - Decimal(str(frozen)))
    budget.spent_amount = (budget.spent_amount or Decimal(0)) + Decimal(str(actual_amount))
    _sync_remaining(budget)
    _assert_invariants(budget, "release")

    wo.frozen_amount = Decimal(0)
    wo.remaining_frozen = Decimal(0)

    from app.core.audit import log_business_event
    log_business_event(
        db, "BUDGET_RELEASED", "budget", budget.id,
        description=f"שוחרר הקפאה ₪{frozen:,.0f}, הוצאה ₪{actual_amount:,.0f} (WO #{work_order_id})",
        metadata={"work_order_id": work_order_id, "frozen_released": frozen,
                  "actual_spent": actual_amount},
        category="financial",
    )
    db.commit()


def request_budget_transfer(
    from_budget_id: "Optional[int]",
    to_budget_id: int,
    amount: float,
    reason: str,
    requested_by: int,
    transfer_type: str = "regular",
    db: "Session" = None,
) -> "BudgetTransfer":
    """
    יוצר בקשת העברת תקציב בסטטוס PENDING.
    """
    from app.models.budget_transfer import BudgetTransfer
    from datetime import datetime

    transfer = BudgetTransfer(
        from_budget_id=from_budget_id,
        to_budget_id=to_budget_id,
        amount=amount,
        reason=reason,
        requested_by=requested_by,
        transfer_type=transfer_type,
        status="PENDING",
        requested_at=datetime.now(),
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer


def approve_budget_transfer(
    transfer_id: int,
    approved_by: int,
    approved_amount: float,
    db: "Session",
    notes: str = "",
) -> "BudgetTransfer":
    """
    מנהל מרחב מאשר (מלא / חלקי) — מעביר סכום בין תקציבים.
    """
    from app.models.budget import Budget
    from app.models.budget_transfer import BudgetTransfer
    from datetime import datetime

    transfer = db.query(BudgetTransfer).filter(BudgetTransfer.id == transfer_id).first()
    if not transfer:
        raise ValueError("בקשת העברה לא נמצאה")

    if transfer.from_budget_id:
        from_b = db.query(Budget).filter(Budget.id == transfer.from_budget_id).first()
        if from_b:
            avail = float(from_b.remaining_amount or from_b.total_amount or 0)
            if avail < approved_amount:
                raise ValueError(f"אין מספיק יתרה. זמין: ₪{avail:,.0f}")
            from_b.total_amount = float(from_b.total_amount or 0) - approved_amount
            from_b.remaining_amount = float(from_b.remaining_amount or 0) - approved_amount

    to_b = db.query(Budget).filter(Budget.id == transfer.to_budget_id).first()
    if not to_b:
        raise ValueError("תקציב יעד לא נמצא")
    to_b.total_amount = float(to_b.total_amount or 0) + approved_amount
    to_b.remaining_amount = float(to_b.remaining_amount or 0) + approved_amount

    transfer.status = "APPROVED"
    transfer.approved_by = approved_by
    transfer.amount = approved_amount
    transfer.approved_at = datetime.now()
    transfer.executed_at = datetime.now()
    if notes:
        transfer.notes = notes

    db.commit()
    db.refresh(transfer)
    return transfer


def reject_budget_transfer(
    transfer_id: int,
    rejected_by: int,
    reason: str,
    db: "Session",
) -> "BudgetTransfer":
    from app.models.budget_transfer import BudgetTransfer

    transfer = db.query(BudgetTransfer).filter(BudgetTransfer.id == transfer_id).first()
    if not transfer:
        raise ValueError("בקשת העברה לא נמצאה")

    transfer.status = "REJECTED"
    transfer.approved_by = rejected_by
    transfer.rejected_reason = reason
    db.commit()
    db.refresh(transfer)
    return transfer
