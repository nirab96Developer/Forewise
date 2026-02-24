"""
Activity Type Service - לוגיקה עסקית לסוגי פעולות
"""
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.models.activity_type import ActivityType
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundException, DuplicateException


class ActivityTypeService(BaseService[ActivityType]):
    """Activity Type service"""
    
    def __init__(self):
        super().__init__(ActivityType)
    
    def get_by_code(self, db: Session, code: str) -> Optional[ActivityType]:
        """Get activity type by code"""
        query = db.query(ActivityType).filter(ActivityType.code == code)
        # LOOKUP tables use is_active instead of deleted_at
        return query.first()
    
    def list_with_filters(
        self,
        db: Session,
        q: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = True,
        page: int = 1,
        page_size: int = 1000,
        sort_by: str = "sort_order",
        sort_desc: bool = False
    ) -> Tuple[List[ActivityType], int]:
        """List activity types with filters"""
        query = db.query(ActivityType)
        
        # LOOKUP tables don't have deleted_at, they use is_active
        
        # Search
        if q:
            query = query.filter(
                or_(
                    ActivityType.name.ilike(f"%{q}%"),
                    ActivityType.code.ilike(f"%{q}%"),
                    ActivityType.description.ilike(f"%{q}%")
                )
            )
        
        # Category filter
        if category:
            query = query.filter(ActivityType.category == category)
        
        # Active filter
        if is_active is not None:
            query = query.filter(ActivityType.is_active == is_active)
        
        # Count
        total = query.count()
        
        # Sort
        if hasattr(ActivityType, sort_by):
            order_col = getattr(ActivityType, sort_by)
            query = query.order_by(
                order_col.desc() if sort_desc else order_col.asc(),
                ActivityType.id.desc(),
            )
        
        # Paginate
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        return items, total
    
    def create_activity_type(
        self,
        db: Session,
        code: str,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        is_active: bool = True,
        sort_order: int = 0,
        display_order: int = 0
    ) -> ActivityType:
        """Create new activity type"""
        # Validate unique code
        if self.get_by_code(db, code):
            raise DuplicateException(f"Activity type with code '{code}' already exists")
        
        activity_type = ActivityType(
            code=code,
            name=name,
            description=description,
            category=category,
            is_active=is_active,
            sort_order=sort_order,
            display_order=display_order
        )
        
        db.add(activity_type)
        db.commit()
        db.refresh(activity_type)
        
        return activity_type
    
    def update_activity_type(
        self,
        db: Session,
        activity_type_id: int,
        data: Dict[str, Any]
    ) -> ActivityType:
        """Update activity type"""
        activity_type = self.get_by_id(db, activity_type_id)
        if not activity_type:
            raise NotFoundException(f"Activity type {activity_type_id} not found")
        
        # Check unique code if changing
        if 'code' in data and data['code'] != activity_type.code:
            existing = self.get_by_code(db, data['code'])
            if existing:
                raise DuplicateException(f"Activity type with code '{data['code']}' already exists")
        
        for key, value in data.items():
            if hasattr(activity_type, key) and value is not None:
                setattr(activity_type, key, value)
        
        db.commit()
        db.refresh(activity_type)
        
        return activity_type
    
    def deactivate(self, db: Session, activity_type_id: int) -> ActivityType:
        """Deactivate activity type (soft delete via is_active=False)"""
        activity_type = self.get_by_id(db, activity_type_id)
        if not activity_type:
            raise NotFoundException(f"Activity type {activity_type_id} not found")
        
        activity_type.is_active = False
        db.commit()
        db.refresh(activity_type)
        
        return activity_type
    
    def activate(self, db: Session, activity_type_id: int) -> ActivityType:
        """Activate activity type"""
        activity_type = self.get_by_id(db, activity_type_id)
        if not activity_type:
            raise NotFoundException(f"Activity type {activity_type_id} not found")
        
        activity_type.is_active = True
        db.commit()
        db.refresh(activity_type)
        
        return activity_type
    
    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """Get activity type statistics"""
        total = db.query(func.count(ActivityType.id)).scalar() or 0
        active = db.query(func.count(ActivityType.id)).filter(
            ActivityType.is_active == True
        ).scalar() or 0
        
        # By category
        by_category = db.query(
            ActivityType.category,
            func.count(ActivityType.id)
        ).group_by(ActivityType.category).all()
        
        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "by_category": {cat or "uncategorized": count for cat, count in by_category}
        }


# Singleton
activity_type_service = ActivityTypeService()
