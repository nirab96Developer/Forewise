"""
Region Service
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.models.region import Region
from app.schemas.region import RegionCreate, RegionUpdate, RegionSearch, RegionStatistics
from app.services.base_service import BaseService
from app.core.exceptions import DuplicateException


class RegionService(BaseService[Region]):
    """Region Service - CORE"""
    
    def __init__(self):
        super().__init__(Region)
    
    def create(self, db: Session, data: RegionCreate, current_user_id: int) -> Region:
        """Create region"""
        # Validate UNIQUE: name
        existing = db.query(Region).filter(
            func.lower(Region.name) == func.lower(data.name),
            Region.deleted_at.is_(None)
        ).first()
        if existing:
            raise DuplicateException(f"Region '{data.name}' already exists")
        
        # Validate UNIQUE: code (if provided)
        if data.code:
            existing = db.query(Region).filter(
                Region.code == data.code,
                Region.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Region code '{data.code}' already exists")
        
        # Create
        region_dict = data.model_dump(exclude_unset=True)
        region = Region(**region_dict)
        
        db.add(region)
        db.commit()
        db.refresh(region)
        return region
    
    def update(self, db: Session, region_id: int, data: RegionUpdate, current_user_id: int) -> Region:
        """Update region"""
        region = self.get_by_id_or_404(db, region_id)
        
        # Version check
        if data.version is not None and region.version != data.version:
            raise DuplicateException("Region was modified by another user")
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        # Validate UNIQUE: name (if changed)
        if 'name' in update_dict and update_dict['name'] and update_dict['name'] != region.name:
            existing = db.query(Region).filter(
                func.lower(Region.name) == func.lower(update_dict['name']),
                Region.id != region_id,
                Region.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Region '{update_dict['name']}' already exists")
        
        # Validate UNIQUE: code (if changed)
        if 'code' in update_dict and update_dict['code'] and update_dict['code'] != region.code:
            existing = db.query(Region).filter(
                Region.code == update_dict['code'],
                Region.id != region_id,
                Region.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Region code '{update_dict['code']}' already exists")
        
        # Update
        for field, value in update_dict.items():
            setattr(region, field, value)
        
        if region.version is not None:
            region.version += 1
        
        db.commit()
        db.refresh(region)
        return region
    
    def list(self, db: Session, search: RegionSearch) -> Tuple[List[Region], int]:
        """List regions"""
        query = self._base_query(db, include_deleted=search.include_deleted)
        
        if search.q:
            term = f"%{search.q}%"
            query = query.where(or_(
                Region.name.ilike(term),
                Region.code.ilike(term),
                Region.description.ilike(term)
            ))
        
        if search.is_active is not None:
            query = query.where(Region.is_active == search.is_active)
        
        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        
        sort_col = getattr(Region, search.sort_by, Region.name)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        offset = (search.page - 1) * search.page_size
        regions = db.execute(query.offset(offset).limit(search.page_size)).scalars().all()
        
        return regions, total
    
    def get_by_code(self, db: Session, code: str) -> Optional[Region]:
        """Get by code"""
        return db.execute(
            select(Region).where(Region.code == code, Region.deleted_at.is_(None))
        ).scalar_one_or_none()
    
    def get_statistics(self, db: Session) -> RegionStatistics:
        """Get statistics"""
        query = select(Region).where(Region.deleted_at.is_(None))
        regions = db.execute(query).scalars().all()
        
        return RegionStatistics(
            total=len(regions),
            active_count=sum(1 for r in regions if r.is_active)
        )
