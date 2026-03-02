"""
Users Router - API endpoints למשתמשים
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserBrief,
    UserListResponse,
    UserSearch,
    UserPasswordChange,
    UserLock
)
from app.services.user_service import user_service

router = APIRouter(prefix="/users", tags=["users"])


# ============================================================================
# List & Get
# ============================================================================

@router.get("", response_model=UserListResponse)
def list_users(
    filters: Annotated[UserSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """רשימת משתמשים"""
    require_permission(current_user, "users.list")
    
    users, total = user_service.list_with_filters(db, filters)
    
    total_pages = (total + filters.page_size - 1) // filters.page_size
    
    return UserListResponse(
        items=users,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=total_pages
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """קבלת משתמש לפי ID"""
    require_permission(current_user, "users.read")
    
    user = user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


# ============================================================================
# Create & Update
# ============================================================================

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """יצירת משתמש חדש"""
    require_permission(current_user, "users.create")

    user = user_service.create_user(db, user_data)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """עדכון משתמש"""
    require_permission(current_user, "users.update")
    
    user = user_service.update_user(db, user_id, user_data)
    return user


# ============================================================================
# Delete
# ============================================================================

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """מחיקת משתמש (soft delete)"""
    require_permission(current_user, "users.delete")
    
    user_service.soft_delete(db, user_id)
    return None


# ============================================================================
# Special Actions
# ============================================================================

@router.post("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    user_id: int,
    password_data: UserPasswordChange,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """החלפת סיסמה"""
    # User can change own password, or admin can change any
    if user_id != current_user.id:
        require_permission(current_user, "users.manage")
    
    user_service.change_password(
        db,
        user_id,
        password_data.current_password,
        password_data.new_password
    )
    return None


@router.post("/{user_id}/lock", response_model=UserResponse)
def lock_user(
    user_id: int,
    lock_data: UserLock,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """נעילת משתמש"""
    require_permission(current_user, "users.lock")
    
    user = user_service.lock_user(db, user_id, lock_data.locked_until)
    return user


@router.post("/{user_id}/unlock", response_model=UserResponse)
def unlock_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """ביטול נעילת משתמש"""
    require_permission(current_user, "users.unlock")
    
    user = user_service.unlock_user(db, user_id)
    return user
