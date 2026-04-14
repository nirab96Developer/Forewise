"""
Permissions Router - API endpoints להרשאות
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.permission import (
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
    PermissionListResponse,
    PermissionSearch
)
from app.services.permission_service import permission_service

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("", response_model=PermissionListResponse)
def list_permissions(
    filters: Annotated[PermissionSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """רשימת הרשאות"""
    require_permission(current_user, "permissions.list")
    
    permissions, total = permission_service.list_with_filters(db, filters)
    total_pages = (total + filters.page_size - 1) // filters.page_size
    
    return PermissionListResponse(
        items=permissions,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=total_pages
    )


@router.get("/{permission_id}", response_model=PermissionResponse)
def get_permission(
    permission_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """קבלת הרשאה"""
    require_permission(current_user, "permissions.read")
    
    permission = permission_service.get_by_id(db, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    return permission


@router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
def create_permission(
    permission_data: PermissionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """יצירת הרשאה"""
    require_permission(current_user, "permissions.create")
    
    permission = permission_service.create_permission(db, permission_data)
    return permission


@router.put("/{permission_id}", response_model=PermissionResponse)
def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """עדכון הרשאה"""
    require_permission(current_user, "permissions.update")
    
    permission = permission_service.update_permission(db, permission_id, permission_data)
    return permission


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(
    permission_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """מחיקת הרשאה"""
    require_permission(current_user, "permissions.delete")
    
    permission_service.soft_delete(db, permission_id)
    return None
