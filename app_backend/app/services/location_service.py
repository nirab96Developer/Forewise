"""
Location Service
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.models.location import Location
from app.models.area import Area
from app.schemas.location import LocationCreate, LocationUpdate, LocationSearch, LocationStatistics
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException


class LocationService:
    """Location Service - CORE"""
    
    def get_by_id(self, db: Session, id: int) -> Optional[Location]:
        """Get by ID"""
        return db.query(Location).filter(
            Location.id == id,
            Location.deleted_at.is_(None)
        ).first()
    
    def get_by_id_or_404(self, db: Session, id: int) -> Location:
        """Get by ID or raise"""
        item = self.get_by_id(db, id)
        if not item:
            raise NotFoundException(f"Location {id} not found")
        return item
    
    def create(self, db: Session, data: LocationCreate, current_user_id: int) -> Location:
        """Create"""
        # Validate FK: area_id
        area = db.query(Area).filter(
            Area.id == data.area_id,
            Area.deleted_at.is_(None)
        ).first()
        if not area:
            raise ValidationException(f"Area {data.area_id} not found")
        
        # Validate UNIQUE: code
        existing = db.query(Location).filter(
            func.lower(Location.code) == func.lower(data.code),
            Location.deleted_at.is_(None)
        ).first()
        if existing:
            raise DuplicateException(f"Location code '{data.code}' already exists")
        
        # Create
        item_dict = data.model_dump(exclude_unset=True)
        item = Location(**item_dict)
        
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    
    def update(self, db: Session, item_id: int, data: LocationUpdate, current_user_id: int) -> Location:
        """Update"""
        item = self.get_by_id_or_404(db, item_id)
        
        # Version check
        if data.version is not None and item.version != data.version:
            raise DuplicateException("Item was modified by another user")
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        # Validate FK: area_id (if changed)
        if 'area_id' in update_dict and update_dict['area_id']:
            area = db.query(Area).filter(
                Area.id == update_dict['area_id'],
                Area.deleted_at.is_(None)
            ).first()
            if not area:
                raise ValidationException(f"Area {update_dict['area_id']} not found")
        
        # Validate UNIQUE: code (if changed)
        if 'code' in update_dict and update_dict['code'] and update_dict['code'] != item.code:
            existing = db.query(Location).filter(
                func.lower(Location.code) == func.lower(update_dict['code']),
                Location.id != item_id,
                Location.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Location code '{update_dict['code']}' already exists")
        
        # Update
        for field, value in update_dict.items():
            setattr(item, field, value)
        
        if item.version is not None:
            item.version += 1
        
        db.commit()
        db.refresh(item)
        return item
    
    def list(self, db: Session, search: LocationSearch) -> Tuple[List[Location], int]:
        """List"""
        query = select(Location)
        
        if not search.include_deleted:
            query = query.where(Location.deleted_at.is_(None))
        
        if search.q:
            term = f"%{search.q}%"
            query = query.where(or_(
                Location.name.ilike(term),
                Location.code.ilike(term),
                Location.description.ilike(term),
                Location.address.ilike(term)
            ))
        
        if search.area_id is not None:
            query = query.where(Location.area_id == search.area_id)
        
        if search.is_active is not None:
            query = query.where(Location.is_active == search.is_active)
        
        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        
        sort_col = getattr(Location, search.sort_by, Location.name)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        offset = (search.page - 1) * search.page_size
        items = db.execute(query.offset(offset).limit(search.page_size)).scalars().all()
        
        return items, total
    
    def get_by_code(self, db: Session, code: str) -> Optional[Location]:
        """Get by code"""
        return db.execute(
            select(Location).where(
                func.lower(Location.code) == func.lower(code),
                Location.deleted_at.is_(None)
            )
        ).scalar_one_or_none()
    
    def soft_delete(self, db: Session, item_id: int, current_user_id: int) -> Location:
        """Soft delete"""
        item = self.get_by_id_or_404(db, item_id)
        from datetime import datetime
        item.deleted_at = datetime.utcnow()
        item.is_active = False
        db.commit()
        db.refresh(item)
        return item
    
    def restore(self, db: Session, item_id: int, current_user_id: int) -> Location:
        """Restore"""
        item = db.query(Location).filter(
            Location.id == item_id
        ).first()
        if not item:
            raise NotFoundException(f"Location {item_id} not found")
        item.deleted_at = None
        item.is_active = True
        db.commit()
        db.refresh(item)
        return item
    
    def get_statistics(self, db: Session) -> LocationStatistics:
        """Get statistics"""
        items = db.execute(
            select(Location).where(Location.deleted_at.is_(None))
        ).scalars().all()
        
        return LocationStatistics(
            total=len(items),
            active_count=sum(1 for i in items if i.is_active)
        )
