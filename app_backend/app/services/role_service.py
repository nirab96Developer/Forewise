"""
Role Service - לוגיקה עסקית לתפקידים
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func

from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.schemas.role import RoleCreate, RoleUpdate, RoleSearch
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundException, DuplicateException


class RoleService(BaseService[Role]):
    """Role service"""
    
    def __init__(self):
        super().__init__(Role)
    
    def get_by_code(self, db: Session, code: str) -> Optional[Role]:
        """קבלת תפקיד לפי code"""
        query = self._base_query(db).where(Role.code == code.upper())
        return db.execute(query).scalar_one_or_none()
    
    def list_with_filters(
        self,
        db: Session,
        filters: RoleSearch
    ) -> Tuple[List[Role], int]:
        """רשימת תפקידים עם פילטרים - optimized with eager loading"""
        # Use eager loading for permissions
        query = self._base_query(db).options(
            joinedload(Role.permissions)
        )
        
        filter_conditions = []
        
        if filters.code:
            filter_conditions.append(Role.code.ilike(f"%{filters.code}%"))
        
        if filters.name:
            filter_conditions.append(Role.name.ilike(f"%{filters.name}%"))
        
        if filters.is_active is not None:
            filter_conditions.append(Role.is_active == filters.is_active)
        
        # Apply filters
        for condition in filter_conditions:
            query = query.where(condition)
        
        # Count - simple query without eager loading
        count_query = select(func.count(Role.id))
        if self._has_deleted_at:
            count_query = count_query.where(Role.deleted_at.is_(None))
        for condition in filter_conditions:
            count_query = count_query.where(condition)
        total = db.execute(count_query).scalar() or 0
        
        # Sort
        if filters.sort_by and hasattr(Role, filters.sort_by):
            order_col = getattr(Role, filters.sort_by)
            query = query.order_by(order_col.desc() if filters.sort_desc else order_col.asc())
        
        # Paginate
        offset = (filters.page - 1) * filters.page_size
        query = query.offset(offset).limit(filters.page_size)
        
        roles = db.execute(query).scalars().unique().all()
        
        return roles, total
    
    def create_role(self, db: Session, role_data: RoleCreate) -> Role:
        """יצירת תפקיד"""
        # Validate code unique
        if self.get_by_code(db, role_data.code):
            raise DuplicateException(f"Role with code {role_data.code} already exists")
        
        return self.create(db, role_data.model_dump())
    
    def update_role(self, db: Session, role_id: int, role_data: RoleUpdate) -> Role:
        """עדכון תפקיד"""
        return self.update(db, role_id, role_data.model_dump(exclude_unset=True, exclude_none=True))
    
    def assign_permission(
        self,
        db: Session,
        role_id: int,
        permission_id: int
    ) -> None:
        """הקצאת הרשאה לתפקיד"""
        # Validate role exists
        self.get_by_id_or_404(db, role_id)
        
        # Validate permission exists
        permission = db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            raise NotFoundException(f"Permission {permission_id} not found")
        
        # Check if already assigned
        existing = db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        ).first()
        
        if existing:
            raise DuplicateException("Permission already assigned to role")
        
        # Create assignment
        assignment = RolePermission(
            role_id=role_id,
            permission_id=permission_id
        )
        db.add(assignment)
        db.commit()
    
    def remove_permission(
        self,
        db: Session,
        role_id: int,
        permission_id: int
    ) -> None:
        """הסרת הרשאה מתפקיד"""
        assignment = db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        ).first()
        
        if not assignment:
            raise NotFoundException("Permission assignment not found")
        
        db.delete(assignment)
        db.commit()
    
    def list_role_permissions(
        self,
        db: Session,
        role_id: int
    ) -> List[Permission]:
        """רשימת הרשאות לתפקיד"""
        role = self.get_by_id_or_404(db, role_id)
        return role.permissions


# Singleton
role_service = RoleService()
