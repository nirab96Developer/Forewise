"""
Equipment Category Service
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.models.equipment_category import EquipmentCategory
from app.schemas.equipment_category import (
    EquipmentCategoryCreate, EquipmentCategoryUpdate,
    EquipmentCategorySearch, EquipmentCategoryStatistics
)
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException


class EquipmentCategoryService:
    """Equipment Category Service - CORE with soft delete"""
    
    def get_by_id(self, db: Session, id: int) -> Optional[EquipmentCategory]:
        """Get by ID"""
        return db.query(EquipmentCategory).filter(
            EquipmentCategory.id == id,
            EquipmentCategory.deleted_at.is_(None)
        ).first()
    
    def get_by_id_or_404(self, db: Session, id: int) -> EquipmentCategory:
        """Get by ID or raise"""
        item = self.get_by_id(db, id)
        if not item:
            raise NotFoundException(f"Equipment category {id} not found")
        return item
    
    def create(self, db: Session, data: EquipmentCategoryCreate, current_user_id: int) -> EquipmentCategory:
        """Create"""
        # Validate UNIQUE: code
        existing = db.query(EquipmentCategory).filter(
            func.lower(EquipmentCategory.code) == func.lower(data.code),
            EquipmentCategory.deleted_at.is_(None)
        ).first()
        if existing:
            raise DuplicateException(f"Equipment category code '{data.code}' already exists")
        
        # Validate UNIQUE: name
        existing = db.query(EquipmentCategory).filter(
            func.lower(EquipmentCategory.name) == func.lower(data.name),
            EquipmentCategory.deleted_at.is_(None)
        ).first()
        if existing:
            raise DuplicateException(f"Equipment category name '{data.name}' already exists")
        
        # Validate FK: parent_category_id (self-ref)
        if data.parent_category_id:
            parent = db.query(EquipmentCategory).filter(
                EquipmentCategory.id == data.parent_category_id,
                EquipmentCategory.deleted_at.is_(None)
            ).first()
            if not parent:
                raise ValidationException(f"Parent category {data.parent_category_id} not found")
        
        # Create
        item_dict = data.model_dump(exclude_unset=True)
        item = EquipmentCategory(**item_dict)
        
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    
    def update(self, db: Session, item_id: int, data: EquipmentCategoryUpdate, current_user_id: int) -> EquipmentCategory:
        """Update"""
        item = self.get_by_id_or_404(db, item_id)
        
        # Version check
        if data.version is not None and item.version != data.version:
            raise DuplicateException("Item was modified by another user")
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        # Validate UNIQUE: code (if changed)
        if 'code' in update_dict and update_dict['code'] and update_dict['code'] != item.code:
            existing = db.query(EquipmentCategory).filter(
                func.lower(EquipmentCategory.code) == func.lower(update_dict['code']),
                EquipmentCategory.id != item_id,
                EquipmentCategory.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Equipment category code '{update_dict['code']}' already exists")
        
        # Validate UNIQUE: name (if changed)
        if 'name' in update_dict and update_dict['name'] and update_dict['name'] != item.name:
            existing = db.query(EquipmentCategory).filter(
                func.lower(EquipmentCategory.name) == func.lower(update_dict['name']),
                EquipmentCategory.id != item_id,
                EquipmentCategory.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Equipment category name '{update_dict['name']}' already exists")
        
        # Validate FK: parent_category_id (self-ref)
        if 'parent_category_id' in update_dict and update_dict['parent_category_id']:
            if update_dict['parent_category_id'] == item_id:
                raise ValidationException("Category cannot be its own parent")
            parent = db.query(EquipmentCategory).filter(
                EquipmentCategory.id == update_dict['parent_category_id'],
                EquipmentCategory.deleted_at.is_(None)
            ).first()
            if not parent:
                raise ValidationException(f"Parent category {update_dict['parent_category_id']} not found")
        
        # Update
        for field, value in update_dict.items():
            setattr(item, field, value)
        
        item.version += 1
        
        db.commit()
        db.refresh(item)
        return item
    
    def list(self, db: Session, search: EquipmentCategorySearch) -> Tuple[List[EquipmentCategory], int]:
        """List"""
        query = select(EquipmentCategory)
        
        if not search.include_deleted:
            query = query.where(EquipmentCategory.deleted_at.is_(None))
        
        if search.q:
            term = f"%{search.q}%"
            query = query.where(or_(
                EquipmentCategory.name.ilike(term),
                EquipmentCategory.code.ilike(term),
                EquipmentCategory.description.ilike(term)
            ))
        
        if search.parent_category_id is not None:
            query = query.where(EquipmentCategory.parent_category_id == search.parent_category_id)
        
        if search.requires_license is not None:
            query = query.where(EquipmentCategory.requires_license == search.requires_license)
        
        if search.requires_certification is not None:
            query = query.where(EquipmentCategory.requires_certification == search.requires_certification)
        
        if search.is_active is not None:
            query = query.where(EquipmentCategory.is_active == search.is_active)
        
        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        
        sort_col = getattr(EquipmentCategory, search.sort_by, EquipmentCategory.name)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        offset = (search.page - 1) * search.page_size
        items = db.execute(query.offset(offset).limit(search.page_size)).scalars().all()
        
        return items, total
    
    def get_by_code(self, db: Session, code: str) -> Optional[EquipmentCategory]:
        """Get by code"""
        return db.execute(
            select(EquipmentCategory).where(
                func.lower(EquipmentCategory.code) == func.lower(code),
                EquipmentCategory.deleted_at.is_(None)
            )
        ).scalar_one_or_none()
    
    def get_children(self, db: Session, parent_id: int) -> List[EquipmentCategory]:
        """Get child categories"""
        return db.execute(
            select(EquipmentCategory).where(
                EquipmentCategory.parent_category_id == parent_id,
                EquipmentCategory.deleted_at.is_(None)
            )
        ).scalars().all()
    
    def soft_delete(self, db: Session, item_id: int, current_user_id: int) -> EquipmentCategory:
        """Soft delete - blocks if has active children"""
        item = self.get_by_id_or_404(db, item_id)
        
        # Check for active children
        children = self.get_children(db, item_id)
        if children:
            raise ValidationException(f"Cannot delete category with {len(children)} active children")
        
        from datetime import datetime
        item.deleted_at = datetime.utcnow()
        item.is_active = False
        db.commit()
        db.refresh(item)
        return item
    
    def restore(self, db: Session, item_id: int, current_user_id: int) -> EquipmentCategory:
        """Restore"""
        item = db.query(EquipmentCategory).filter(
            EquipmentCategory.id == item_id
        ).first()
        if not item:
            raise NotFoundException(f"Equipment category {item_id} not found")
        item.deleted_at = None
        item.is_active = True
        db.commit()
        db.refresh(item)
        return item
    
    def get_statistics(self, db: Session) -> EquipmentCategoryStatistics:
        """Get statistics"""
        items = db.execute(
            select(EquipmentCategory).where(EquipmentCategory.deleted_at.is_(None))
        ).scalars().all()
        
        return EquipmentCategoryStatistics(
            total=len(items),
            active_count=sum(1 for i in items if i.is_active),
            root_count=sum(1 for i in items if i.parent_category_id is None)
        )
