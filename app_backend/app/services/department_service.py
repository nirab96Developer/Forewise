"""
Department Service
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentSearch, DepartmentStatistics
from app.services.base_service import BaseService
from app.core.exceptions import ValidationException, DuplicateException


class DepartmentService(BaseService[Department]):
    """Department Service - CORE"""
    
    def __init__(self):
        super().__init__(Department)
    
    def create(self, db: Session, data: DepartmentCreate, current_user_id: int) -> Department:
        """Create department"""
        # Validate UNIQUE: code
        existing = db.query(Department).filter(
            func.lower(Department.code) == func.lower(data.code),
            Department.deleted_at.is_(None)
        ).first()
        if existing:
            raise DuplicateException(f"Department code '{data.code}' already exists")
        
        # Validate FK: parent_department_id (self-ref)
        if data.parent_department_id:
            parent = db.query(Department).filter(
                Department.id == data.parent_department_id,
                Department.deleted_at.is_(None)
            ).first()
            if not parent:
                raise ValidationException(f"Parent department {data.parent_department_id} not found")
        
        # Create
        dept_dict = data.model_dump(exclude_unset=True)
        dept = Department(**dept_dict)
        
        db.add(dept)
        db.commit()
        db.refresh(dept)
        return dept
    
    def update(self, db: Session, dept_id: int, data: DepartmentUpdate, current_user_id: int) -> Department:
        """Update department"""
        dept = self.get_by_id_or_404(db, dept_id)
        
        # Version check
        if data.version is not None and dept.version != data.version:
            raise DuplicateException("Department was modified by another user")
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        # Validate UNIQUE: code (if changed)
        if 'code' in update_dict and update_dict['code'] and update_dict['code'] != dept.code:
            existing = db.query(Department).filter(
                func.lower(Department.code) == func.lower(update_dict['code']),
                Department.id != dept_id,
                Department.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Department code '{update_dict['code']}' already exists")
        
        # Validate FK: parent_department_id
        if 'parent_department_id' in update_dict and update_dict['parent_department_id']:
            if update_dict['parent_department_id'] == dept_id:
                raise ValidationException("Department cannot be its own parent")
            parent = db.query(Department).filter(
                Department.id == update_dict['parent_department_id'],
                Department.deleted_at.is_(None)
            ).first()
            if not parent:
                raise ValidationException(f"Parent department {update_dict['parent_department_id']} not found")
        
        # Update
        for field, value in update_dict.items():
            setattr(dept, field, value)
        
        if dept.version is not None:
            dept.version += 1
        
        db.commit()
        db.refresh(dept)
        return dept
    
    def list(self, db: Session, search: DepartmentSearch) -> Tuple[List[Department], int]:
        """List departments"""
        query = self._base_query(db, include_deleted=search.include_deleted)
        
        if search.q:
            term = f"%{search.q}%"
            query = query.where(or_(
                Department.name.ilike(term),
                Department.code.ilike(term),
                Department.description.ilike(term)
            ))
        
        if search.parent_department_id is not None:
            query = query.where(Department.parent_department_id == search.parent_department_id)
        
        if search.is_active is not None:
            query = query.where(Department.is_active == search.is_active)
        
        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        
        sort_col = getattr(Department, search.sort_by, Department.name)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        offset = (search.page - 1) * search.page_size
        depts = db.execute(query.offset(offset).limit(search.page_size)).scalars().all()
        
        return depts, total
    
    def get_by_code(self, db: Session, code: str) -> Optional[Department]:
        """Get by code"""
        return db.execute(
            select(Department).where(
                func.lower(Department.code) == func.lower(code),
                Department.deleted_at.is_(None)
            )
        ).scalar_one_or_none()
    
    def get_children(self, db: Session, parent_id: int) -> List[Department]:
        """Get child departments"""
        return db.execute(
            select(Department).where(
                Department.parent_department_id == parent_id,
                Department.deleted_at.is_(None)
            )
        ).scalars().all()
    
    def get_statistics(self, db: Session) -> DepartmentStatistics:
        """Get statistics"""
        query = select(Department).where(Department.deleted_at.is_(None))
        depts = db.execute(query).scalars().all()
        
        return DepartmentStatistics(
            total=len(depts),
            active_count=sum(1 for d in depts if d.is_active),
            root_count=sum(1 for d in depts if d.parent_department_id is None)
        )
