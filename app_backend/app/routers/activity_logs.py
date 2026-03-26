# app/routers/activity_logs.py
"""Activity log endpoints with role-based scoping.

Scope levels:
- MY: user sees only their own activity (all users)
- AREA: area manager sees all activity in their area
- REGION: region manager sees all activity in their region
- SYSTEM: admin sees everything
"""
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
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
        "REGION_MANAGER": "region",
        "AREA_MANAGER": "area",
    }
    return scope_map.get(role_code, "my")


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
        from datetime import timedelta
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
            query = query.filter(ActivityLog.category.in_(["financial", "system"]))
        elif role_code == "WORK_MANAGER":
            query = query.filter(ActivityLog.category.in_(["operational", "system"]))
        elif role_code == "ORDER_COORDINATOR":
            query = query.filter(ActivityLog.category.in_(["operational", "system"]))
    
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
    """Get a specific activity log by ID."""
    log = db.query(ActivityLog).filter(ActivityLog.id == log_id).first()
    if not log:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity log not found"
        )
    
    return log

