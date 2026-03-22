"""
Roles Router - API endpoints לתפקידים
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleBrief,
    RoleListResponse,
    RoleSearch,
    RolePermissionAssign,
    PermissionBrief
)
from app.services.role_service import role_service

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=RoleListResponse)
def list_roles(
    filters: Annotated[RoleSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """רשימת תפקידים"""
    require_permission(current_user, "roles.list")

    from sqlalchemy import text as sa_text
    user_counts: dict = {}
    for query in [
        "SELECT role_id, COUNT(*) FROM user_roles GROUP BY role_id",
        "SELECT role_id, COUNT(*) FROM users WHERE role_id IS NOT NULL AND is_active = true GROUP BY role_id",
    ]:
        try:
            rows = db.execute(sa_text(query)).fetchall()
            user_counts = {r[0]: r[1] for r in rows}
            break
        except Exception:
            db.rollback()

    roles, total = role_service.list_with_filters(db, filters)
    total_pages = (total + filters.page_size - 1) // filters.page_size

    items = []
    for role in roles:
        role.__dict__['user_count'] = user_counts.get(role.id, 0)
        items.append(role)

    return RoleListResponse(
        items=items,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=total_pages
    )


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """קבלת תפקיד"""
    require_permission(current_user, "roles.read")
    
    role = role_service.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return role


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    role_data: RoleCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """יצירת תפקיד"""
    require_permission(current_user, "roles.create")
    
    role = role_service.create_role(db, role_data)
    return role


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """עדכון תפקיד"""
    require_permission(current_user, "roles.update")
    
    role = role_service.update_role(db, role_id, role_data)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """מחיקת תפקיד"""
    require_permission(current_user, "roles.delete")
    
    role_service.soft_delete(db, role_id)
    return None


@router.post("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def assign_permission_to_role(
    role_id: int,
    permission_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """הקצאת הרשאה לתפקיד"""
    require_permission(current_user, "roles.manage_permissions")
    
    role_service.assign_permission(db, role_id, permission_id)
    return None


@router.delete("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """הסרת הרשאה מתפקיד"""
    require_permission(current_user, "roles.manage_permissions")
    
    role_service.remove_permission(db, role_id, permission_id)
    return None


@router.get("/{role_id}/permissions", response_model=List[PermissionBrief])
def list_role_permissions(
    role_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """רשימת הרשאות לתפקיד"""
    require_permission(current_user, "roles.read")
    
    permissions = role_service.list_role_permissions(db, role_id)
    return permissions
