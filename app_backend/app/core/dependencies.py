# app/core/dependencies.py
"""FastAPI dependencies with real permission checking."""
from typing import Annotated, Optional, List, Set
from functools import lru_cache
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger

from app.core.config import settings
from app.core.database import get_db

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)


# ============================================================
# Permission Cache (in-memory, refreshes per request)
# ============================================================
_permissions_cache: dict = {}


def get_user_permissions(db: Session, role_id: int) -> Set[str]:
    """Get all permission codes for a role from the database."""
    if role_id in _permissions_cache:
        return _permissions_cache[role_id]
    
    result = db.execute(text("""
        SELECT p.code 
        FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        WHERE rp.role_id = :role_id AND p.is_active = TRUE
    """), {"role_id": role_id})
    
    permissions = {row[0] for row in result}
    _permissions_cache[role_id] = permissions
    
    logger.debug(f"[PERMISSIONS] Role {role_id} has {len(permissions)} permissions: {permissions}")
    return permissions


def clear_permissions_cache():
    """Clear the permissions cache (call after role/permission changes)."""
    global _permissions_cache
    _permissions_cache = {}


# ============================================================
# User Authentication
# ============================================================
async def get_current_user(
        db: Annotated[Session, Depends(get_db)],
        token: Annotated[Optional[str], Depends(oauth2_scheme)]
):
    """Get current authenticated user with role and permissions."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # Load role relationship
    if user.role_id:
        from app.models.role import Role
        user.role = db.query(Role).filter(Role.id == user.role_id).first()
        # Load permissions for the role
        user._permissions = get_user_permissions(db, user.role_id)
    else:
        user._permissions = set()

    return user


async def get_current_active_user(
        current_user: Annotated[object, Depends(get_current_user)]
):
    """Ensure user is active."""
    if not getattr(current_user, 'is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


# ============================================================
# Permission Checking
# ============================================================
def user_has_permission(user, permission: str) -> bool:
    """Check if user has a specific permission.
    
    ADMIN role has all permissions.
    Other roles checked against role_permissions from DB.
    Case-insensitive: 'WORK_ORDERS.CREATE' matches 'work_orders.create'.
    """
    # ADMIN bypass - has all permissions
    if hasattr(user, 'role') and user.role and user.role.code == 'ADMIN':
        return True
    
    # Check cached permissions
    user_perms = getattr(user, '_permissions', set())
    
    # Normalize to lower for comparison
    perm_lower = permission.lower()
    perms_lower = {p.lower() for p in user_perms}
    
    # Direct match (case-insensitive)
    if perm_lower in perms_lower:
        return True
    
    # Check SYSTEM.ADMIN (super permission)
    if 'system.admin' in perms_lower:
        return True
    
    return False


class PermissionChecker:
    """Check specific permissions - FastAPI dependency."""

    def __init__(self, *permissions: str, require_all: bool = False):
        """
        Args:
            permissions: One or more permission codes (e.g., 'PROJECTS.VIEW', 'PROJECTS.CREATE')
            require_all: If True, all permissions required. If False, any one is enough.
        """
        self.permissions = permissions
        self.require_all = require_all

    async def __call__(
            self,
            current_user: Annotated[object, Depends(get_current_active_user)],
            db: Annotated[Session, Depends(get_db)]
    ):
        # Ensure permissions are loaded
        if not hasattr(current_user, '_permissions'):
            if current_user.role_id:
                current_user._permissions = get_user_permissions(db, current_user.role_id)
            else:
                current_user._permissions = set()
        
        # Check permissions
        if self.require_all:
            # All permissions required
            has_all = all(user_has_permission(current_user, p) for p in self.permissions)
            if not has_all:
                missing = [p for p in self.permissions if not user_has_permission(current_user, p)]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permissions: {', '.join(missing)}"
                )
        else:
            # Any permission is enough
            has_any = any(user_has_permission(current_user, p) for p in self.permissions)
            if not has_any:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these permissions required: {', '.join(self.permissions)}"
                )
        
        return current_user


def require_permission(user_or_first_perm, *permissions: str, require_all: bool = False):
    """
    Dual-mode permission check:

    Inline mode (most common in this codebase):
        require_permission(current_user, "users.list")
        require_permission(current_user, "perm1", "perm2")
raises HTTP 403 immediately if not authorized, returns user if OK

    Factory/Depends mode:
        Depends(require_permission("PROJECTS.VIEW"))
returns a PermissionChecker callable for FastAPI dependency injection
    """
    # Detect inline mode: first arg is a user object (has role_id attribute)
    if hasattr(user_or_first_perm, 'role_id') or hasattr(user_or_first_perm, 'is_active'):
        user = user_or_first_perm
        # ADMIN bypass
        if hasattr(user, 'role') and user.role and getattr(user.role, 'code', None) == 'ADMIN':
            return user
        if not permissions:
            return user
        if require_all:
            for perm in permissions:
                if not user_has_permission(user, perm):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Missing permission: {perm}"
                    )
        else:
            if not any(user_has_permission(user, p) for p in permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these permissions required: {', '.join(permissions)}"
                )
        return user
    else:
# Factory mode: require_permission("perm1", "perm2") PermissionChecker for Depends
        all_perms = (user_or_first_perm,) + permissions
        return PermissionChecker(*all_perms, require_all=require_all)


# ============================================================
# Safe Mode - Block Write Operations in Production
# ============================================================
def require_write_access():
    """
    Block all write operations (POST/PUT/PATCH/DELETE) when SAFE_MODE is enabled.
    Use this dependency on any endpoint that modifies data.
    
    Usage:
        @router.post("/items")
        async def create_item(
            _: None = Depends(require_write_access()),
            user: User = Depends(get_current_active_user)
        ):
            ...
    """
    async def check_safe_mode():
        if settings.SAFE_MODE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
detail=" SAFE MODE: Write operations are disabled. Contact admin to enable writes."
            )
        return None
    return check_safe_mode


# ============================================================
# Role-based Dependencies (shortcuts)
# ============================================================
async def admin_required(
        current_user: Annotated[object, Depends(get_current_active_user)]
):
    """Require admin privileges."""
    if hasattr(current_user, 'role') and current_user.role:
        if current_user.role.code not in ['ADMIN', 'SUPER_ADMIN']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def manager_required(
        current_user: Annotated[object, Depends(get_current_active_user)]
):
    """Require manager privileges."""
    allowed_roles = ['ADMIN', 'SUPER_ADMIN', 'REGION_MANAGER', 'AREA_MANAGER', 'WORK_MANAGER']
    if hasattr(current_user, 'role') and current_user.role:
        if current_user.role.code not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Manager privileges required"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager privileges required"
        )
    return current_user


def require_admin():
    """Require admin privileges."""
    return Depends(admin_required)


def require_manager():
    """Require manager privileges."""
    return Depends(manager_required)


# ============================================================
# Pagination
# ============================================================
def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(None, ge=1, le=200, description="Items per page"),
    page_size: int = Query(None, ge=1, le=200, description="Items per page (alias for per_page)"),
    sort_by: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order")
):
    """Get pagination parameters."""
    from app.schemas.common import PaginationParams
    items_per_page = per_page or page_size or 50
    return PaginationParams(page=page, page_size=min(items_per_page, 200))


# ============================================================
# Project Access Check
# ============================================================
async def check_project_access(
    project_id: int,
    current_user: Annotated[object, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """Check if user has access to a specific project.
    
    - ADMIN: access to all projects
    - REGION_MANAGER: access to projects in their region
    - AREA_MANAGER: access to projects in their area
    - Others: access to assigned projects
    """
    from app.models.project import Project
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # ADMIN can access everything
    if hasattr(current_user, 'role') and current_user.role and current_user.role.code == 'ADMIN':
        return current_user
    
    # REGION_MANAGER - check region
    if hasattr(current_user, 'role') and current_user.role and current_user.role.code == 'REGION_MANAGER':
        if hasattr(current_user, 'region_id') and project.region_id:
            if current_user.region_id == project.region_id:
                return current_user
    
    # AREA_MANAGER - check area
    if hasattr(current_user, 'role') and current_user.role and current_user.role.code == 'AREA_MANAGER':
        if hasattr(current_user, 'area_id') and project.area_id:
            if current_user.area_id == project.area_id:
                return current_user
    
    # For now, allow access (TODO: implement assignment-based access)
    return current_user


# ============================================================
# Type Aliases for Common Dependencies
# ============================================================
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[object, Depends(get_current_user)]
CurrentActiveUser = Annotated[object, Depends(get_current_active_user)]
AdminUser = Annotated[object, Depends(admin_required)]
ManagerUser = Annotated[object, Depends(manager_required)]
DatabaseSession = Annotated[Session, Depends(get_db)]
