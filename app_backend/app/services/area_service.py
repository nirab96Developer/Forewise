"""
Area Service
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_

from app.models.area import Area
from app.models.region import Region
from app.schemas.area import AreaCreate, AreaUpdate, AreaSearch, AreaStatistics
from app.services.base_service import BaseService
from app.core.exceptions import ValidationException, DuplicateException


class AreaService(BaseService[Area]):
    """Area Service - CORE"""
    
    def __init__(self):
        super().__init__(Area)
    
    def create(self, db: Session, data: AreaCreate, current_user_id: int) -> Area:
        """Create area"""
        # Validate FK: region_id
        if data.region_id:
            region = db.query(Region).filter(
                Region.id == data.region_id,
                Region.deleted_at.is_(None)
            ).first()
            if not region:
                raise ValidationException(f"Region {data.region_id} not found")
        
        # Validate UNIQUE: name (within region)
        existing = db.query(Area).filter(
            func.lower(Area.name) == func.lower(data.name),
            Area.region_id == data.region_id,
            Area.deleted_at.is_(None)
        ).first()
        if existing:
            raise DuplicateException(f"Area '{data.name}' already exists in this region")
        
        # Validate UNIQUE: code (if provided)
        if data.code:
            existing = db.query(Area).filter(
                Area.code == data.code,
                Area.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Area code '{data.code}' already exists")
        
        # Create
        area_dict = data.model_dump(exclude_unset=True)
        area = Area(**area_dict)
        
        db.add(area)
        db.commit()
        db.refresh(area)
        return area
    
    def update(self, db: Session, area_id: int, data: AreaUpdate, current_user_id: int) -> Area:
        """Update area"""
        area = self.get_by_id_or_404(db, area_id)
        
        # Version check
        if data.version is not None and area.version != data.version:
            raise DuplicateException("Area was modified by another user")
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        # Validate FK: region_id (if changed)
        if 'region_id' in update_dict and update_dict['region_id']:
            region = db.query(Region).filter(
                Region.id == update_dict['region_id'],
                Region.deleted_at.is_(None)
            ).first()
            if not region:
                raise ValidationException(f"Region {update_dict['region_id']} not found")
        
        # Validate UNIQUE: name (if changed)
        new_region = update_dict.get('region_id', area.region_id)
        if 'name' in update_dict and update_dict['name'] and update_dict['name'] != area.name:
            existing = db.query(Area).filter(
                func.lower(Area.name) == func.lower(update_dict['name']),
                Area.region_id == new_region,
                Area.id != area_id,
                Area.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Area '{update_dict['name']}' already exists in this region")
        
        # Validate UNIQUE: code (if changed)
        if 'code' in update_dict and update_dict['code'] and update_dict['code'] != area.code:
            existing = db.query(Area).filter(
                Area.code == update_dict['code'],
                Area.id != area_id,
                Area.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Area code '{update_dict['code']}' already exists")
        
        # Update
        for field, value in update_dict.items():
            setattr(area, field, value)
        
        if area.version is not None:
            area.version += 1
        
        db.commit()
        db.refresh(area)
        return area
    
    def list(self, db: Session, search: AreaSearch) -> Tuple[List[Area], int]:
        """List areas — uses selectinload to avoid N+1 on region/manager."""
        query = self._base_query(db, include_deleted=search.include_deleted)

        # Eager-load relationships in a single query to eliminate N+1
        query = query.options(
            selectinload(Area.region),
            selectinload(Area.manager),
        )

        if search.q:
            term = f"%{search.q}%"
            query = query.where(or_(
                Area.name.ilike(term),
                Area.code.ilike(term),
                Area.description.ilike(term)
            ))

        if search.region_id is not None:
            query = query.where(Area.region_id == search.region_id)

        if search.is_active is not None:
            query = query.where(Area.is_active == search.is_active)

        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

        sort_col = getattr(Area, search.sort_by, Area.name)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())

        offset = (search.page - 1) * search.page_size
        areas = db.execute(query.offset(offset).limit(search.page_size)).scalars().all()

        return areas, total
    
    def get_by_code(self, db: Session, code: str) -> Optional[Area]:
        """Get by code"""
        return db.execute(
            select(Area).where(Area.code == code, Area.deleted_at.is_(None))
        ).scalar_one_or_none()
    
    def get_statistics(self, db: Session) -> AreaStatistics:
        """Get statistics"""
        query = select(Area).where(Area.deleted_at.is_(None))
        areas = db.execute(query).scalars().all()
        
        return AreaStatistics(
            total=len(areas),
            active_count=sum(1 for a in areas if a.is_active)
        )
