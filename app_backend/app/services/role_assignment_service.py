"""
RoleAssignment Service - לוגיקה עסקית להקצאת תפקידים
"""
from datetime import datetime
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.role_assignment import RoleAssignment
from app.models.user import User
from app.models.role import Role
from app.schemas.role_assignment import RoleAssignmentCreate, RoleAssignmentSearch
from app.core.exceptions import NotFoundException, DuplicateException


class RoleAssignmentService:
    """RoleAssignment service"""
    
    def assign_role_to_user(
        self,
        db: Session,
        assignment_data: RoleAssignmentCreate,
        assigned_by_id: int
    ) -> RoleAssignment:
        """הקצאת תפקיד למשתמש"""
        # Validate user exists
        user = db.query(User).filter(User.id == assignment_data.user_id).first()
        if not user:
            raise NotFoundException(f"User {assignment_data.user_id} not found")
        
        # Validate role exists
        role = db.query(Role).filter(Role.id == assignment_data.role_id).first()
        if not role:
            raise NotFoundException(f"Role {assignment_data.role_id} not found")
        
        # Check if already assigned (same user, role, scope)
        existing = db.query(RoleAssignment).filter(
            and_(
                RoleAssignment.user_id == assignment_data.user_id,
                RoleAssignment.role_id == assignment_data.role_id,
                RoleAssignment.scope_type == assignment_data.scope_type,
                RoleAssignment.scope_id == assignment_data.scope_id,
                RoleAssignment.is_active == True
            )
        ).first()
        
        if existing:
            raise DuplicateException("Role already assigned to user with this scope")
        
        # Create assignment
        assignment = RoleAssignment(
            **assignment_data.model_dump(),
            assigned_by=assigned_by_id,
            assigned_at=datetime.utcnow()
        )
        
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        
        return assignment
    
    def remove_role_from_user(
        self,
        db: Session,
        user_id: int,
        role_id: int,
        scope_type: str = "GLOBAL",
        scope_id: Optional[int] = None
    ) -> None:
        """הסרת תפקיד ממשתמש"""
        assignment = db.query(RoleAssignment).filter(
            and_(
                RoleAssignment.user_id == user_id,
                RoleAssignment.role_id == role_id,
                RoleAssignment.scope_type == scope_type,
                RoleAssignment.scope_id == scope_id
            )
        ).first()
        
        if not assignment:
            raise NotFoundException("Role assignment not found")
        
        # Deactivate instead of delete
        assignment.is_active = False
        db.commit()
    
    def list_user_roles(self, db: Session, user_id: int) -> List[RoleAssignment]:
        """רשימת תפקידים של משתמש"""
        return db.query(RoleAssignment).filter(
            RoleAssignment.user_id == user_id,
            RoleAssignment.is_active == True
        ).all()
    
    def list_role_users(self, db: Session, role_id: int) -> List[RoleAssignment]:
        """רשימת משתמשים עם תפקיד"""
        return db.query(RoleAssignment).filter(
            RoleAssignment.role_id == role_id,
            RoleAssignment.is_active == True
        ).all()
    
    def list_with_filters(
        self,
        db: Session,
        filters: RoleAssignmentSearch
    ) -> Tuple[List[RoleAssignment], int]:
        """רשימה עם פילטרים"""
        query = db.query(RoleAssignment)
        
        if filters.user_id:
            query = query.filter(RoleAssignment.user_id == filters.user_id)
        
        if filters.role_id:
            query = query.filter(RoleAssignment.role_id == filters.role_id)
        
        if filters.scope_type:
            query = query.filter(RoleAssignment.scope_type == filters.scope_type)
        
        if filters.is_active is not None:
            query = query.filter(RoleAssignment.is_active == filters.is_active)
        
        total = query.count()
        
        offset = (filters.page - 1) * filters.page_size
        assignments = query.offset(offset).limit(filters.page_size).all()
        
        return assignments, total


# Singleton
role_assignment_service = RoleAssignmentService()

