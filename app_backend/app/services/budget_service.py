"""
Budget Service
"""

from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
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
