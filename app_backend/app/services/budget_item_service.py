"""
BudgetItem Service
"""

from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.models.budget_item import BudgetItem
from app.models.budget import Budget
from app.schemas.budget_item import BudgetItemCreate, BudgetItemUpdate, BudgetItemSearch, BudgetItemStatistics
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException


class BudgetItemService(BaseService[BudgetItem]):
    """BudgetItem Service - CORE"""
    
    def __init__(self):
        super().__init__(BudgetItem)
    
    def create(self, db: Session, data: BudgetItemCreate, current_user_id: int) -> BudgetItem:
        """Create budget item"""
        # Validate FK: budget_id
        budget = db.query(Budget).filter_by(id=data.budget_id).first()
        if not budget:
            raise ValidationException(f"Budget {data.budget_id} not found")
        if not budget.is_active:
            raise ValidationException(f"Budget {data.budget_id} is not active")
        
        # Create
        item_dict = data.model_dump(exclude_unset=True)
        item = BudgetItem(**item_dict)
        
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    
    def update(self, db: Session, item_id: int, data: BudgetItemUpdate, current_user_id: int) -> BudgetItem:
        """Update budget item"""
        item = self.get_by_id_or_404(db, item_id)
        
        # Version check
        if data.version is not None and item.version != data.version:
            raise DuplicateException("Budget item was modified by another user")
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        for field, value in update_dict.items():
            setattr(item, field, value)
        
        if item.version is not None:
            item.version += 1
        
        db.commit()
        db.refresh(item)
        return item
    
    def list(self, db: Session, search: BudgetItemSearch) -> Tuple[List[BudgetItem], int]:
        """List budget items"""
        query = self._base_query(db, include_deleted=search.include_deleted)
        
        if search.q:
            term = f"%{search.q}%"
            query = query.where(or_(
                BudgetItem.item_name.ilike(term),
                BudgetItem.item_code.ilike(term),
                BudgetItem.description.ilike(term)
            ))
        
        if search.budget_id:
            query = query.where(BudgetItem.budget_id == search.budget_id)
        if search.item_type:
            query = query.where(BudgetItem.item_type == search.item_type)
        if search.category:
            query = query.where(BudgetItem.category == search.category)
        if search.status:
            query = query.where(BudgetItem.status == search.status)
        if search.is_active is not None:
            query = query.where(BudgetItem.is_active == search.is_active)
        
        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        
        sort_col = getattr(BudgetItem, search.sort_by, BudgetItem.item_name)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        offset = (search.page - 1) * search.page_size
        items = db.execute(query.offset(offset).limit(search.page_size)).scalars().all()
        
        return items, total
    
    def get_statistics(self, db: Session, budget_id: Optional[int] = None) -> BudgetItemStatistics:
        """Get statistics"""
        query = select(BudgetItem).where(BudgetItem.deleted_at.is_(None))
        
        if budget_id:
            query = query.where(BudgetItem.budget_id == budget_id)
        
        items = db.execute(query).scalars().all()
        
        return BudgetItemStatistics(
            total=len(items),
            total_planned=sum(i.planned_amount for i in items),
            total_approved=sum(i.approved_amount or 0 for i in items),
            total_actual=sum(i.actual_amount or 0 for i in items),
            by_status={}
        )
