"""
Supplier Constraint Reason Service
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from collections import defaultdict

from app.models.supplier_constraint_reason import SupplierConstraintReason
from app.schemas.supplier_constraint_reason import (
    SupplierConstraintReasonCreate, SupplierConstraintReasonUpdate,
    SupplierConstraintReasonSearch, SupplierConstraintReasonStatistics
)
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException


class SupplierConstraintReasonService:
    """Supplier Constraint Reason Service - LOOKUP with soft delete"""
    
    def get_by_id(self, db: Session, id: int) -> Optional[SupplierConstraintReason]:
        """Get by ID"""
        return db.query(SupplierConstraintReason).filter(
            SupplierConstraintReason.id == id,
            SupplierConstraintReason.deleted_at.is_(None)
        ).first()
    
    def get_by_id_or_404(self, db: Session, id: int) -> SupplierConstraintReason:
        """Get by ID or raise"""
        item = self.get_by_id(db, id)
        if not item:
            raise NotFoundException(f"Supplier constraint reason {id} not found")
        return item
    
    def create(self, db: Session, data: SupplierConstraintReasonCreate, current_user_id: int) -> SupplierConstraintReason:
        """Create"""
        # Validate UNIQUE: code
        existing = db.query(SupplierConstraintReason).filter(
            func.lower(SupplierConstraintReason.code) == func.lower(data.code),
            SupplierConstraintReason.deleted_at.is_(None)
        ).first()
        if existing:
            raise DuplicateException(f"Supplier constraint reason code '{data.code}' already exists")
        
        # Create
        item_dict = data.model_dump(exclude_unset=True)
        item = SupplierConstraintReason(**item_dict)
        
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    
    def update(self, db: Session, item_id: int, data: SupplierConstraintReasonUpdate, current_user_id: int) -> SupplierConstraintReason:
        """Update"""
        item = self.get_by_id_or_404(db, item_id)
        
        # Version check
        if data.version is not None and item.version != data.version:
            raise DuplicateException("Item was modified by another user")
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        # Validate UNIQUE: code (if changed)
        if 'code' in update_dict and update_dict['code'] and update_dict['code'] != item.code:
            existing = db.query(SupplierConstraintReason).filter(
                func.lower(SupplierConstraintReason.code) == func.lower(update_dict['code']),
                SupplierConstraintReason.id != item_id,
                SupplierConstraintReason.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Supplier constraint reason code '{update_dict['code']}' already exists")
        
        # Update
        for field, value in update_dict.items():
            setattr(item, field, value)
        
        item.version += 1
        
        db.commit()
        db.refresh(item)
        return item
    
    def list(self, db: Session, search: SupplierConstraintReasonSearch) -> Tuple[List[SupplierConstraintReason], int]:
        """List"""
        query = select(SupplierConstraintReason)
        
        if not search.include_deleted:
            query = query.where(SupplierConstraintReason.deleted_at.is_(None))
        
        if search.q:
            term = f"%{search.q}%"
            query = query.where(or_(
                SupplierConstraintReason.name_he.ilike(term),
                SupplierConstraintReason.name_en.ilike(term),
                SupplierConstraintReason.code.ilike(term),
                SupplierConstraintReason.description.ilike(term)
            ))
        
        if search.category:
            query = query.where(SupplierConstraintReason.category == search.category)
        
        if search.requires_approval is not None:
            query = query.where(SupplierConstraintReason.requires_approval == search.requires_approval)
        
        if search.is_active is not None:
            query = query.where(SupplierConstraintReason.is_active == search.is_active)
        
        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        
        sort_col = getattr(SupplierConstraintReason, search.sort_by, SupplierConstraintReason.display_order)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        offset = (search.page - 1) * search.page_size
        items = db.execute(query.offset(offset).limit(search.page_size)).scalars().all()
        
        return items, total
    
    def get_by_code(self, db: Session, code: str) -> Optional[SupplierConstraintReason]:
        """Get by code"""
        return db.execute(
            select(SupplierConstraintReason).where(
                func.lower(SupplierConstraintReason.code) == func.lower(code),
                SupplierConstraintReason.deleted_at.is_(None)
            )
        ).scalar_one_or_none()
    
    def soft_delete(self, db: Session, item_id: int, current_user_id: int) -> SupplierConstraintReason:
        """Soft delete"""
        item = self.get_by_id_or_404(db, item_id)
        from datetime import datetime
        item.deleted_at = datetime.utcnow()
        item.is_active = False
        db.commit()
        db.refresh(item)
        return item
    
    def restore(self, db: Session, item_id: int, current_user_id: int) -> SupplierConstraintReason:
        """Restore"""
        item = db.query(SupplierConstraintReason).filter(
            SupplierConstraintReason.id == item_id
        ).first()
        if not item:
            raise NotFoundException(f"Supplier constraint reason {item_id} not found")
        item.deleted_at = None
        item.is_active = True
        db.commit()
        db.refresh(item)
        return item
    
    def get_statistics(self, db: Session) -> SupplierConstraintReasonStatistics:
        """Get statistics"""
        items = db.execute(
            select(SupplierConstraintReason).where(SupplierConstraintReason.deleted_at.is_(None))
        ).scalars().all()
        
        by_category = defaultdict(int)
        for item in items:
            by_category[item.category] += 1
        
        return SupplierConstraintReasonStatistics(
            total=len(items),
            active_count=sum(1 for i in items if i.is_active),
            by_category=dict(by_category)
        )
