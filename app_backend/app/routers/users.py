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


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """פרופיל המשתמש הנוכחי"""
    user = user_service.get_by_id(db, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


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


# ── Lifecycle endpoints ────────────────────────────────────────────────────────

from pydantic import BaseModel as _BaseModel
from datetime import datetime as _dt, timedelta as _td
from typing import Optional as _Opt


class SuspendRequest(_BaseModel):
    reason: str
    deletion_years: _Opt[int] = 3


class ChangeRoleRequest(_BaseModel):
    role_id: int
    region_id: _Opt[int] = None
    area_id: _Opt[int] = None


@router.put("/{user_id}/suspend")
def suspend_user(
    user_id: int,
    body: SuspendRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """השהיית משתמש עם תאריך מחיקה מתוזמנת"""
    require_permission(current_user, "users.edit")

    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")

    user.status = "suspended"
    user.suspended_at = _dt.now()
    user.suspension_reason = body.reason
    user.scheduled_deletion_at = _dt.now() + _td(days=365 * body.deletion_years)
    user.is_active = False

    # בטל sessions פעילים
    try:
        from sqlalchemy import text as _text
        db.execute(_text("DELETE FROM otp_tokens WHERE user_id = :uid"), {"uid": user_id})
    except Exception:
        pass

    db.commit()
    db.refresh(user)

    # רשום audit
    try:
        from app.models.audit_log import AuditLog
        db.add(AuditLog(
            user_id=current_user.id, table_name="users", record_id=user_id,
            action="SUSPEND",
            new_values={"reason": body.reason, "scheduled_deletion_at": str(user.scheduled_deletion_at)},
        ))
        db.commit()
    except Exception:
        pass

    return {
        "id": user.id,
        "status": user.status,
        "suspended_at": user.suspended_at,
        "scheduled_deletion_at": user.scheduled_deletion_at,
        "message": "המשתמש הושהה בהצלחה",
    }


@router.put("/{user_id}/reactivate")
def reactivate_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """החזרת משתמש מושהה לפעילות"""
    require_permission(current_user, "users.edit")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")

    user.status = "active"
    user.is_active = True
    user.suspended_at = None
    user.suspension_reason = None
    user.scheduled_deletion_at = None
    db.commit()
    return {"id": user.id, "status": user.status, "message": "המשתמש הופעל מחדש"}


@router.put("/{user_id}/role")
def change_user_role(
    user_id: int,
    body: ChangeRoleRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """שינוי תפקיד משתמש + ניקוי שיוכי פרויקטים ישנים"""
    require_permission(current_user, "users.edit")

    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")

    # שמור previous role
    user.previous_role_id = user.role_id
    user.role_id = body.role_id
    user.region_id = body.region_id
    user.area_id = body.area_id

    # בטל שיוכי פרויקטים ישנים
    try:
        from app.models.project_assignment import ProjectAssignment
        db.query(ProjectAssignment).filter(
            ProjectAssignment.user_id == user_id,
            ProjectAssignment.is_active == True
        ).update({"is_active": False}, synchronize_session=False)
    except Exception:
        pass

    db.commit()
    db.refresh(user)

    # audit
    try:
        from app.models.audit_log import AuditLog
        db.add(AuditLog(
            user_id=current_user.id, table_name="users", record_id=user_id,
            action="CHANGE_ROLE",
            old_values={"role_id": user.previous_role_id},
            new_values={"role_id": body.role_id, "region_id": body.region_id, "area_id": body.area_id},
        ))
        db.commit()
    except Exception:
        pass

    return {
        "id": user.id,
        "role_id": user.role_id,
        "previous_role_id": user.previous_role_id,
        "region_id": user.region_id,
        "area_id": user.area_id,
        "message": "התפקיד עודכן בהצלחה",
    }
