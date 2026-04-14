"""
Equipment Type Service
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.models.equipment_type import EquipmentType
from app.schemas.equipment_type import EquipmentTypeCreate, EquipmentTypeUpdate, EquipmentTypeSearch, EquipmentTypeStatistics
from app.core.exceptions import NotFoundException, DuplicateException


class EquipmentTypeService:
    """Equipment Type Service - LOOKUP"""
    
    def get_by_id(self, db: Session, id: int) -> Optional[EquipmentType]:
        """Get by ID"""
        return db.query(EquipmentType).filter(EquipmentType.id == id).first()
    
    def get_by_id_or_404(self, db: Session, id: int) -> EquipmentType:
        """Get by ID or raise"""
        item = self.get_by_id(db, id)
        if not item:
            raise NotFoundException(f"Equipment type {id} not found")
        return item
    
    def create(self, db: Session, data: EquipmentTypeCreate, current_user_id: int) -> EquipmentType:
        """Create equipment type"""
        # Validate UNIQUE: code
        existing = db.query(EquipmentType).filter(
            func.lower(EquipmentType.code) == func.lower(data.code)
        ).first()
        if existing:
            raise DuplicateException(f"Equipment type code '{data.code}' already exists")
        
        # Create
        item_dict = data.model_dump(exclude_unset=True)
        item = EquipmentType(**item_dict)
        
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    
    def update(self, db: Session, item_id: int, data: EquipmentTypeUpdate, current_user_id: int) -> EquipmentType:
        """Update equipment type"""
        item = self.get_by_id_or_404(db, item_id)
        
        update_dict = data.model_dump(exclude_unset=True)
        
        # Validate UNIQUE: code (if changed)
        if 'code' in update_dict and update_dict['code'] and update_dict['code'] != item.code:
            existing = db.query(EquipmentType).filter(
                func.lower(EquipmentType.code) == func.lower(update_dict['code']),
                EquipmentType.id != item_id
            ).first()
            if existing:
                raise DuplicateException(f"Equipment type code '{update_dict['code']}' already exists")
        
        # Update
        for field, value in update_dict.items():
            setattr(item, field, value)
        
        db.commit()
        db.refresh(item)
        return item
    
    def list(self, db: Session, search: EquipmentTypeSearch) -> Tuple[List[EquipmentType], int]:
        """List equipment types"""
        query = select(EquipmentType)
        
        if search.q:
            term = f"%{search.q}%"
            query = query.where(or_(
                EquipmentType.name.ilike(term),
                EquipmentType.code.ilike(term),
                EquipmentType.description.ilike(term)
            ))
        
        if search.category:
            query = query.where(EquipmentType.category == search.category)
        
        if search.is_active is not None:
            query = query.where(EquipmentType.is_active == search.is_active)
        
        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        
        sort_col = getattr(EquipmentType, search.sort_by, EquipmentType.sort_order)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        offset = (search.page - 1) * search.page_size
        items = db.execute(query.offset(offset).limit(search.page_size)).scalars().all()
        
        return items, total
    
    def get_by_code(self, db: Session, code: str) -> Optional[EquipmentType]:
        """Get by code"""
        return db.execute(
            select(EquipmentType).where(
                func.lower(EquipmentType.code) == func.lower(code)
            )
        ).scalar_one_or_none()
    
    def deactivate(self, db: Session, item_id: int, current_user_id: int) -> EquipmentType:
        """Deactivate"""
        item = self.get_by_id_or_404(db, item_id)
        item.is_active = False
        db.commit()
        db.refresh(item)
        return item
    
    def activate(self, db: Session, item_id: int, current_user_id: int) -> EquipmentType:
        """Activate"""
        item = self.get_by_id_or_404(db, item_id)
        item.is_active = True
        db.commit()
        db.refresh(item)
        return item
    
    def get_statistics(self, db: Session) -> EquipmentTypeStatistics:
        """Get statistics"""
        items = db.execute(select(EquipmentType)).scalars().all()
        
        return EquipmentTypeStatistics(
            total=len(items),
            active_count=sum(1 for i in items if i.is_active)
        )
