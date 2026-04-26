# app/routers/activity_logs.py
"""Activity log endpoints with role-based scoping.

Scope levels:
- MY: user sees only their own activity (all users)
- AREA: area manager sees all activity in their area
- REGION: region manager sees all activity in their region
- SYSTEM: admin sees everything
"""
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.schemas.activity_log import ActivityLogResponse

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


def _get_scope_for_role(role_code: str) -> str:
    """Determine max scope level for a role."""
    scope_map = {
        "ADMIN": "system",
        "SUPER_ADMIN": "system",
        "REGION_MANAGER": "region",
        "AREA_MANAGER": "area",
    }
    return scope_map.get(role_code, "my")


def _user_can_see_log(db: Session, user: User, log: ActivityLog) -> bool:
    """Per-row scope predicate for the detail endpoint.

    Mirrors the list endpoint's filtering rules so a user who can't
    see a log in the list also can't open it by ID. Phase 3 Wave 2.1.a
    closes the legacy gap where /activity-logs/{id} returned any row
    to any authenticated caller.

    Behavior:
      - Owner (`log.user_id == user.id`) always passes — same as list,
        which always includes own activity in the "my" path.
      - ADMIN / SUPER_ADMIN: system scope — see everything.
      - REGION_MANAGER: see logs from users in their region.
      - AREA_MANAGER:   see logs from users in their area.
      - everyone else:  own logs only.
      - Category auto-filter (matches list's "no category specified"
        branch): ACCOUNTANT sees financial/system; WORK_MANAGER and
        ORDER_COORDINATOR see operational/system. Logs outside that
        category set are filtered out (return False).
    """
    role_code = (user.role.code if user.role else "").upper()

    if log.category:
        if role_code == "ACCOUNTANT" and log.category not in ("financial", "system"):
            return False
        if role_code == "WORK_MANAGER" and log.category not in ("operational", "system"):
            return False
        if role_code == "ORDER_COORDINATOR" and log.category not in ("operational", "system"):
            return False

    if log.user_id is not None and log.user_id == user.id:
        return True

    max_scope = _get_scope_for_role(role_code)
    if max_scope == "system":
        return True

    if max_scope == "region":
        if not user.region_id or log.user_id is None:
            return False
        log_user = db.query(User).filter(User.id == log.user_id).first()
        return bool(log_user and log_user.region_id == user.region_id)

    if max_scope == "area":
        if not user.area_id or log.user_id is None:
            return False
        log_user = db.query(User).filter(User.id == log.user_id).first()
        return bool(log_user and log_user.area_id == user.area_id)

    return False


@router.get("/")
async def get_activity_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_id: Optional[int] = None,
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    action: Optional[str] = None,
    scope: Optional[str] = Query(None, description="Scope: my, area, region, system"),
    category: Optional[str] = Query(None, description="Filter by category: operational, financial, management, system"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get activity logs with role-based scoping.
    
    Scopes:
    - my: only current user's activities (available to all)
    - area: all activities in user's area (area_manager+)
    - region: all activities in user's region (region_manager+)
    - system: all activities (admin only)
    
    Categories:
    - operational: הזמנות, ציוד, פרויקטים
    - financial: חשבוניות, תקציב, תשלומים  
    - management: משתמשים, הרשאות, הגדרות
    - system: התחברות, כללי
    """
    query = db.query(ActivityLog)
    
    # Apply date filters
    if start_date:
        query = query.filter(ActivityLog.created_at >= start_date)
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(ActivityLog.created_at <= end_datetime)
    if action:
        query = query.filter(ActivityLog.action.ilike(f"%{action}%"))
    if project_id:
        query = query.filter(ActivityLog.entity_type == 'project', ActivityLog.entity_id == project_id)
    
    # Category filter
    if category:
        query = query.filter(ActivityLog.category == category)
    
    # Determine role and max allowed scope
    role_code = current_user.role.code.upper() if current_user.role else ""
    max_scope = _get_scope_for_role(role_code)
    
    # Determine effective scope (requested vs max allowed)
    scope_hierarchy = ["my", "area", "region", "system"]
    requested_scope = scope if scope in scope_hierarchy else max_scope
    max_idx = scope_hierarchy.index(max_scope)
    req_idx = scope_hierarchy.index(requested_scope)
    effective_scope = requested_scope if req_idx <= max_idx else max_scope
    
    # Apply scope-based filtering
    if effective_scope == "my":
        query = query.filter(ActivityLog.user_id == current_user.id)
    elif effective_scope == "area":
        if current_user.area_id:
            area_user_ids = [u.id for u in db.query(User.id).filter(
                User.area_id == current_user.area_id, User.is_active == True
            ).all()]
            if area_user_ids:
                query = query.filter(ActivityLog.user_id.in_(area_user_ids))
            else:
                query = query.filter(ActivityLog.user_id == current_user.id)
        else:
            query = query.filter(ActivityLog.user_id == current_user.id)
    elif effective_scope == "region":
        if current_user.region_id:
            region_user_ids = [u.id for u in db.query(User.id).filter(
                User.region_id == current_user.region_id, User.is_active == True
            ).all()]
            if region_user_ids:
                query = query.filter(ActivityLog.user_id.in_(region_user_ids))
            else:
                query = query.filter(ActivityLog.user_id == current_user.id)
        else:
            query = query.filter(ActivityLog.user_id == current_user.id)
    # system scope = no user filter (admin sees all)
    
    # Explicit user_id filter overrides scope
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    
    # Auto-filter categories by role when no category specified
    if not category:
        if role_code == "ACCOUNTANT":
            query = query.filter(or_(ActivityLog.category.in_(["financial", "system"]), ActivityLog.category.is_(None)))
        elif role_code == "WORK_MANAGER":
            query = query.filter(or_(ActivityLog.category.in_(["operational", "system"]), ActivityLog.category.is_(None)))
        elif role_code == "ORDER_COORDINATOR":
            query = query.filter(or_(ActivityLog.category.in_(["operational", "system"]), ActivityLog.category.is_(None)))
    
    query = query.order_by(ActivityLog.created_at.desc())
    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [ActivityLogResponse.from_orm(log) for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{log_id}", response_model=ActivityLogResponse)
async def get_activity_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific activity log by ID.

    Phase 3 Wave 2.1.a — same scope as the list endpoint. Without
    this check, any authenticated user could read any log row by
    guessing IDs (G4 in PHASE3_WAVE2_RECON.md).
    """
    from fastapi import HTTPException, status

    log = db.query(ActivityLog).filter(ActivityLog.id == log_id).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity log not found"
        )

    if not _user_can_see_log(db, current_user, log):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to view this activity log"
        )

    return log

