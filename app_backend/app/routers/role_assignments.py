"""
RoleAssignments Router - API endpoints להקצאת תפקידים
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.role_assignment import (
    RoleAssignmentCreate,
    RoleAssignmentResponse
)
from app.services.role_assignment_service import role_assignment_service

router = APIRouter(prefix="/role-assignments", tags=["role-assignments"])


@router.post("", response_model=RoleAssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_role(
    assignment_data: RoleAssignmentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """הקצאת תפקיד למשתמש"""
    require_permission(current_user, "role_assignments.create")
    
    assignment = role_assignment_service.assign_role_to_user(
        db,
        assignment_data,
        assigned_by_id=current_user.id
    )
    return assignment


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def remove_role_assignment(
    user_id: int,
    role_id: int,
    scope_type: str = "GLOBAL",
    scope_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """הסרת הקצאת תפקיד"""
    require_permission(current_user, "role_assignments.delete")
    
    role_assignment_service.remove_role_from_user(db, user_id, role_id, scope_type, scope_id)
    return None


@router.get("/users/{user_id}", response_model=List[RoleAssignmentResponse])
def list_user_role_assignments(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """רשימת תפקידים של משתמש"""
    require_permission(current_user, "role_assignments.list")
    
    assignments = role_assignment_service.list_user_roles(db, user_id)
    return assignments


@router.get("/roles/{role_id}", response_model=List[RoleAssignmentResponse])
def list_role_assignments(
    role_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """רשימת משתמשים עם תפקיד"""
    require_permission(current_user, "role_assignments.list")
    
    assignments = role_assignment_service.list_role_users(db, role_id)
    return assignments

