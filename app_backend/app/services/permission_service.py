"""
Permission Service - לוגיקה עסקית להרשאות
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate, PermissionSearch
from app.services.base_service import BaseService
from app.core.exceptions import DuplicateException


class PermissionService(BaseService[Permission]):
    """Permission service"""
    
    def __init__(self):
        super().__init__(Permission)
    
    def get_by_code(self, db: Session, code: str) -> Optional[Permission]:
        """קבלת הרשאה לפי code"""
        query = self._base_query(db).where(Permission.code == code.lower())
        return db.execute(query).scalar_one_or_none()
    
    def list_with_filters(
        self,
        db: Session,
        filters: PermissionSearch
    ) -> Tuple[List[Permission], int]:
        """רשימת הרשאות עם פילטרים"""
        query = self._base_query(db)
        
        if filters.code:
            query = query.where(Permission.code.ilike(f"%{filters.code}%"))
        
        if filters.name:
            query = query.where(Permission.name.ilike(f"%{filters.name}%"))
        
        if filters.resource:
            query = query.where(Permission.resource == filters.resource)
        
        if filters.action:
            query = query.where(Permission.action == filters.action)
        
        if filters.is_active is not None:
            query = query.where(Permission.is_active == filters.is_active)
        
        # Count
        count_query = select(func.count(Permission.id))
        if self._has_deleted_at:
            count_query = count_query.where(Permission.deleted_at.is_(None))
        total = db.execute(count_query).scalar() or 0
        
        # Sort
        if filters.sort_by and hasattr(Permission, filters.sort_by):
            order_col = getattr(Permission, filters.sort_by)
            query = query.order_by(order_col.desc() if filters.sort_desc else order_col.asc())
        
        # Paginate
        offset = (filters.page - 1) * filters.page_size
        query = query.offset(offset).limit(filters.page_size)
        
        permissions = db.execute(query).scalars().all()
        
        return permissions, total
    
    def create_permission(self, db: Session, permission_data: PermissionCreate) -> Permission:
        """יצירת הרשאה"""
        # Validate code unique
        if self.get_by_code(db, permission_data.code):
            raise DuplicateException(f"Permission with code {permission_data.code} already exists")
        
        return self.create(db, permission_data.model_dump())
    
    def update_permission(
        self,
        db: Session,
        permission_id: int,
        permission_data: PermissionUpdate
    ) -> Permission:
        """עדכון הרשאה"""
        return self.update(db, permission_id, permission_data.model_dump(exclude_unset=True, exclude_none=True))


# Singleton
permission_service = PermissionService()
