"""Dashboard Router"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, and_, or_, select, desc, extract, text

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User, Project, Budget, WorkOrder, Region, Area, Location

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)

# ============================================
# MY TASKS - Central "what's waiting for me"
# ============================================
from app.services.pending_tasks_engine import PendingTasksEngine
_pending_engine = PendingTasksEngine()

@router.get("/my-tasks")
async def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get pending tasks, KPIs, actions, and alerts for current user.
    Same endpoint for ALL roles - content varies by role+scope.
    """
    user = db.query(User).options(
        selectinload(User.role),
    ).filter(User.id == current_user.id).first()
    
    role_code = user.role.code if user and user.role else "USER"
    region_id = user.region_id if user else None
    area_id = user.area_id if user else None
    
    return _pending_engine.get_my_tasks(
        db=db,
        user_id=user.id,
        role=role_code,
        region_id=region_id,
        area_id=area_id,
    )

@router.get("/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get dashboard summary data"""
    
    # Load user with relationships
    user = db.query(User).options(
        selectinload(User.role),
        selectinload(User.region),
        selectinload(User.area)
    ).filter(User.id == current_user.id).first()
    
    # Build base queries based on user role
    project_query = db.query(Project)
    budget_query = db.query(Budget)
    
    # Apply role-based filtering
    user_role_code = user.role.code if user.role else ""
    if user_role_code == "WORK_MANAGER":
        # מנהל עבודה רואה רק פרויקטים שהוקצו לו
        project_query = project_query.filter(Project.manager_id == user.id)
    elif user_role_code == "REGION_MANAGER" and user.region_id:
        project_query = project_query.filter(Project.region_id == user.region_id)
        budget_query = budget_query.filter(Budget.region_id == user.region_id)
    elif user_role_code == "AREA_MANAGER" and user.area_id:
        project_query = project_query.filter(Project.area_id == user.area_id)
        budget_query = budget_query.filter(Budget.area_id == user.area_id)
    
    # Get counts
    total_projects = project_query.count()
    # Project model uses is_active boolean, not status string
    active_projects = project_query.filter(Project.is_active == True).count()
    # For completed projects, we check is_active=False (no status column exists)
    completed_projects = project_query.filter(Project.is_active == False).count()
    
    # Get budget totals
    total_budget = db.query(func.sum(Budget.total_amount)).scalar() or 0
    allocated_budget = db.query(func.sum(Budget.allocated_amount)).scalar() or 0
    spent_budget = db.query(func.sum(Budget.spent_amount)).scalar() or 0
    
    # Get entity counts
    regions_count = db.query(Region).count()
    areas_count = db.query(Area).count()
    locations_count = db.query(Location).count()
    
    # Get user counts
    from app.models import User as UserModel
    total_users = db.query(UserModel).count()
    active_users = db.query(UserModel).filter(UserModel.is_active == True).count()
    
    # Get work orders count (pending approvals)
    pending_work_orders = 0
    completed_work_orders = 0
    try:
        pending_work_orders = db.query(WorkOrder).filter(
            WorkOrder.status == "PENDING"
        ).count()
        completed_work_orders = db.query(WorkOrder).filter(
            or_(WorkOrder.status == "completed", WorkOrder.status == "COMPLETED")
        ).count()
    except:
        pass
    
    # Get pending worklogs (reports awaiting approval)
    pending_worklogs = 0
    hours_this_month = 0
    try:
        from app.models import Worklog
        pending_worklogs = db.query(Worklog).filter(
            Worklog.status == "PENDING"
        ).count()
        
        # Get total hours this month
        current_month = datetime.now().month
        current_year = datetime.now().year
        hours_result = db.query(func.sum(Worklog.work_hours)).filter(
            extract('month', Worklog.report_date) == current_month,
            extract('year', Worklog.report_date) == current_year
        ).scalar()
        hours_this_month = float(hours_result) if hours_result else 0
    except Exception as e:
        print(f"Error getting worklog stats: {e}")
        pass
    
    # Get equipment count
    equipment_count = 0
    try:
        from app.models import Equipment
        equipment_count = db.query(Equipment).filter(Equipment.status == "in_use").count()
    except:
        pass
    
    # Get alerts count (budget overruns only - Project model has no planned_end_date)
    alerts_count = 0
    try:
        # Count projects with budget overruns
        overbudget = db.query(Budget).filter(
            and_(
                Budget.spent_amount > Budget.total_amount,
                Budget.total_amount > 0,
                Budget.is_active == True
            )
        ).count()
        alerts_count = overbudget
    except Exception:
        pass
    
    # Get suppliers count
    suppliers_count = 0
    active_suppliers = 0
    try:
        from app.models import Supplier
        suppliers_count = db.query(Supplier).count()
        active_suppliers = db.query(Supplier).filter(Supplier.is_active == True).count()
    except:
        pass
    
    # Get pending invoices
    pending_invoices = 0
    try:
        from app.models import Invoice
        pending_invoices = db.query(Invoice).filter(
            Invoice.status == "PENDING"
        ).count()
    except:
        pass
    
    # Get total equipment count
    total_equipment = 0
    try:
        from app.models import Equipment
        total_equipment = db.query(Equipment).count()
    except:
        pass
    
    # Calculate percentages
    budget_usage_percentage = (spent_budget / total_budget * 100) if total_budget > 0 else 0
    project_completion_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0
    
    return {
        # Frontend expects these fields
        "pending_approvals_count": pending_worklogs,  # Worklogs pending approval
        "pending_work_orders_count": pending_work_orders,  # Work orders pending
        "completed_work_orders_count": completed_work_orders,
        "active_projects_count": active_projects,
        "total_projects_count": total_projects,
        "total_users": total_users,
        "active_users": active_users,
        "total_regions": regions_count,
        "total_areas": areas_count,
        "equipment_in_use_count": equipment_count,
        "hours_month_total": hours_this_month,
        "alerts_count": alerts_count,
        "pending_invoices_count": pending_invoices,
        "suppliers_count": suppliers_count,
        "active_suppliers_count": active_suppliers,
        "total_suppliers_count": suppliers_count,
        "total_equipment_count": total_equipment,
        "expired_contracts_count": 0,  # TODO: Implement when contracts table exists
        
        # Original fields for backward compatibility
        "projects": {
            "total": total_projects,
            "active": active_projects,
            "completed": completed_projects,
            "completion_rate": round(project_completion_rate, 1)
        },
        "budget": {
            "total": float(total_budget),
            "allocated": float(allocated_budget),
            "spent": float(spent_budget),
            "available": float(total_budget - allocated_budget),
            "usage_percentage": round(budget_usage_percentage, 1)
        },
        "entities": {
            "regions": regions_count,
            "areas": areas_count,
            "locations": locations_count
        },
        "user": {
            "name": current_user.full_name,
            "role": current_user.role.name if current_user.role else "USER",
            "region": current_user.region.name if current_user.region else None,
            "area": current_user.area.name if current_user.area else None
        }
    }

@router.get("/map")
async def get_dashboard_map(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get map data for dashboard."""
    from app.models import Location, Project
    
    # Get locations
    locations = []
    if current_user.role.code == "REGION_MANAGER" and current_user.region:
        locs = db.query(Location).filter(Location.region_id == current_user.region_id).limit(50).all()
    elif current_user.role.code == "AREA_MANAGER" and current_user.area:
        locs = db.query(Location).filter(Location.area_id == current_user.area_id).limit(50).all()
    else:
        locs = db.query(Location).limit(50).all()
    
    for loc in locs:
        if loc.latitude and loc.longitude:
            locations.append({
                "id": loc.id,
                "name": loc.name,
                "lat": float(loc.latitude),
                "lng": float(loc.longitude),
                "type": "location"
            })
    
    # Get projects  
    projects = []
    if current_user.role.code == "REGION_MANAGER" and current_user.region:
        projs = db.query(Project).filter(Project.region_id == current_user.region_id).limit(50).all()
    elif current_user.role.code == "AREA_MANAGER" and current_user.area:
        projs = db.query(Project).filter(Project.area_id == current_user.area_id).limit(50).all()
    else:
        projs = db.query(Project).limit(50).all()
    
    for proj in projs:
        # Try to get location from project
        if hasattr(proj, 'location') and proj.location and proj.location.latitude and proj.location.longitude:
            projects.append({
                "id": proj.id,
                "name": proj.name,
                "lat": float(proj.location.latitude),
                "lng": float(proj.location.longitude),
                "type": "project",
                "status": "active" if proj.is_active else "completed"
            })
    
    return {
        "locations": locations,
        "projects": projects,
        "center": {"lat": 31.7683, "lng": 35.2137},
        "zoom": 7
    }


@router.get("/projects")
async def get_dashboard_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Get recent projects for dashboard"""
    
    # Build query with eager loading to prevent lazy loading issues
    # NOTE: budget_id is an Integer column on Project, not a relationship — load Budget separately
    query = db.query(Project).options(
        selectinload(Project.manager),
        selectinload(Project.region),
        selectinload(Project.area),
    )
    
    # Apply role-based filtering
    if current_user.role.code in ("WORK_MANAGER", "FIELD_WORKER"):
        from app.models.project_assignment import ProjectAssignment
        assigned_ids = [
            pa.project_id for pa in
            db.query(ProjectAssignment.project_id)
            .filter(ProjectAssignment.user_id == current_user.id)
            .all()
        ]
        query = query.filter(
            (Project.id.in_(assigned_ids)) | (Project.manager_id == current_user.id)
        )
    elif current_user.role.code == "REGION_MANAGER" and current_user.region_id:
        query = query.filter(Project.region_id == current_user.region_id)
    elif current_user.role.code == "AREA_MANAGER" and current_user.area_id:
        query = query.filter(Project.area_id == current_user.area_id)
    
    # Get recent projects
    projects = query.order_by(desc(Project.updated_at)).limit(limit).all()

    # Load budgets separately to avoid selectinload on Integer column
    budget_ids = [p.budget_id for p in projects if p.budget_id]
    budgets = {}
    if budget_ids:
        for b in db.query(Budget).filter(Budget.id.in_(budget_ids)).all():
            budgets[b.id] = b

    # Also load budgets by project_id for projects without budget_id FK
    project_ids = [p.id for p in projects]
    budgets_by_project = {}
    if project_ids:
        for b in db.query(Budget).filter(Budget.project_id.in_(project_ids), Budget.is_active == True).all():
            budgets_by_project[b.project_id] = b

    def _get_budget(p):
        if p.budget_id and p.budget_id in budgets:
            return budgets[p.budget_id]
        return budgets_by_project.get(p.id)

    from sqlalchemy import text as _text
    geo_map = {}
    if project_ids:
        try:
            geo_rows = db.execute(_text(
                "SELECT id, ST_Y(location_geom::geometry) as lat, ST_X(location_geom::geometry) as lng "
                "FROM projects WHERE id = ANY(:ids) AND location_geom IS NOT NULL"
            ), {"ids": project_ids}).fetchall()
            geo_map = {r[0]: (float(r[1]), float(r[2])) for r in geo_rows}
        except Exception:
            pass

    return [
        {
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "status": "active" if p.is_active else "completed",
            "priority": "medium",
            "progress": 0,
            "manager_name": p.manager.full_name if p.manager else None,
            "region_name": p.region.name if p.region else None,
            "area_name": p.area.name if p.area else None,
            "allocated_budget": float((_get_budget(p).total_amount or 0)) if _get_budget(p) else 0.0,
            "spent_budget": float((_get_budget(p).spent_amount or 0)) if _get_budget(p) else 0.0,
            "budget_status": "active" if (_get_budget(p) and float(_get_budget(p).total_amount or 0) > 0) else "inactive",
            "start_date": p.created_at.isoformat() if p.created_at else None,
            "end_date": None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            "lat": geo_map[p.id][0] if p.id in geo_map else None,
            "lng": geo_map[p.id][1] if p.id in geo_map else None,
        }
        for p in projects
    ]

@router.get("/alerts")
async def get_dashboard_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Get system alerts for dashboard"""
    
    alerts = []
    
    # Note: Project model has no planned_end_date field, so we skip overdue check
    
    # Check for budget overruns (via Budget relationship)
    try:
        overbudget_query = db.query(Budget).filter(
            and_(
                Budget.spent_amount > Budget.total_amount,
                Budget.total_amount > 0,
                Budget.is_active == True
            )
        )
        
        if current_user.role.code == "REGION_MANAGER" and current_user.region_id:
            overbudget_query = overbudget_query.filter(Project.region_id == current_user.region_id)
        elif current_user.role.code == "AREA_MANAGER" and current_user.area_id:
            overbudget_query = overbudget_query.filter(Project.area_id == current_user.area_id)
        
        overbudget_count = overbudget_query.count()
        if overbudget_count > 0:
            alerts.append({
                "type": "error",
                "title": "חריגות תקציב",
                "message": f"יש {overbudget_count} פרויקטים עם חריגה בתקציב",
                "count": overbudget_count
            })
    except Exception:
        pass
    
    # Check for pending work orders
    try:
        pending_wo_count = db.query(WorkOrder).filter(
            WorkOrder.status == "PENDING"
        ).count()
        if pending_wo_count > 5:
            alerts.append({
                "type": "warning",
                "title": "הזמנות עבודה ממתינות",
                "message": f"יש {pending_wo_count} הזמנות עבודה ממתינות לטיפול",
                "count": pending_wo_count
            })
    except Exception:
        pass
    
    return alerts[:limit]

@router.get("/statistics")
async def get_dashboard_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed statistics for dashboard"""
    
    # Build base query
    project_query = db.query(Project)
    
    # Apply role-based filtering
    if current_user.role.code == "REGION_MANAGER" and current_user.region_id:
        project_query = project_query.filter(Project.region_id == current_user.region_id)
    elif current_user.role.code == "AREA_MANAGER" and current_user.area_id:
        project_query = project_query.filter(Project.area_id == current_user.area_id)
    
    # Get project statistics by status (using is_active boolean)
    # Since Project only has is_active, we simplify to active/inactive
    active_count = project_query.filter(Project.is_active == True).count()
    inactive_count = project_query.filter(Project.is_active == False).count()
    status_stats = {
        "active": active_count,
        "completed": inactive_count,
        "planning": 0,
        "approved": 0,
        "on_hold": 0,
        "cancelled": 0
    }
    
    # Project model doesn't have priority field, use default values
    priority_stats = {
        "low": 0,
        "medium": active_count + inactive_count,  # All projects are "medium" priority
        "high": 0,
        "critical": 0
    }
    
    # Get monthly project creation trend (last 6 months)
    six_months_ago = func.date_trunc('month', func.current_date() - text("interval '6 months'"))
    monthly_stats = db.query(
        func.date_trunc('month', Project.created_at).label('month'),
        func.count(Project.id).label('count')
    ).filter(
        Project.created_at >= six_months_ago
    ).group_by('month').order_by('month').all()
    
    monthly_trend = [
        {
            "month": stat.month.strftime('%Y-%m') if stat.month else None,
            "count": stat.count
        }
        for stat in monthly_stats
    ]
    
    return {
        "by_status": status_stats,
        "by_priority": priority_stats,
        "monthly_trend": monthly_trend,
        "total_projects": sum(status_stats.values())
    }

@router.get("/live-counts")
async def get_live_counts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Live counts for badges across all settings/admin pages.
    Used to show "12 active users", "3 pending", etc.
    """
    from app.models import User as U, Project, WorkOrder, Budget, Region, Area, Location
    from app.models.equipment import Equipment
    from app.models.supplier import Supplier
    
    counts = {}
    
    # Users
    counts["users_active"] = db.query(func.count(U.id)).filter(U.is_active == True).scalar() or 0
    counts["users_total"] = db.query(func.count(U.id)).scalar() or 0
    
    # Roles & Permissions
    from app.models.role import Role
    from app.models.permission import Permission
    counts["roles"] = db.query(func.count(Role.id)).filter(Role.is_active == True).scalar() or 0
    counts["permissions"] = db.query(func.count(Permission.id)).filter(Permission.is_active == True).scalar() or 0
    
    # Suppliers
    counts["suppliers_active"] = db.query(func.count(Supplier.id)).filter(Supplier.is_active == True).scalar() or 0
    
    # Equipment
    counts["equipment_total"] = db.query(func.count(Equipment.id)).filter(Equipment.is_active == True).scalar() or 0
    counts["equipment_in_use"] = db.query(func.count(Equipment.id)).filter(Equipment.status == "in_use").scalar() or 0
    
    # Projects
    counts["projects_active"] = db.query(func.count(Project.id)).filter(Project.is_active == True).scalar() or 0
    
    # Regions / Areas
    counts["regions"] = db.query(func.count(Region.id)).scalar() or 0
    counts["areas"] = db.query(func.count(Area.id)).scalar() or 0
    counts["locations"] = db.query(func.count(Location.id)).scalar() or 0
    
    # Budgets
    counts["budgets_total"] = db.query(func.count(Budget.id)).filter(Budget.is_active == True).scalar() or 0
    
    # Budget overruns
    try:
        counts["budgets_overrun"] = db.query(func.count(Budget.id)).filter(
            and_(Budget.spent_amount > Budget.total_amount, Budget.total_amount > 0)
        ).scalar() or 0
    except:
        counts["budgets_overrun"] = 0
    
    # Work Orders by status
    counts["wo_pending"] = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status.in_(["PENDING", "PENDING_SUPPLIER"]), WorkOrder.is_active == True
    ).scalar() or 0
    counts["wo_in_progress"] = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status == "IN_PROGRESS", WorkOrder.is_active == True
    ).scalar() or 0
    counts["wo_no_status"] = db.query(func.count(WorkOrder.id)).filter(
        or_(WorkOrder.status == None, WorkOrder.status == "")
    ).scalar() or 0
    
    # Support tickets
    try:
        from app.models.support_ticket import SupportTicket
        counts["tickets_open"] = db.query(func.count(SupportTicket.id)).filter(
            SupportTicket.status.in_(["open", "in_progress"]), SupportTicket.is_active == True
        ).scalar() or 0
    except:
        counts["tickets_open"] = 0
    
    # System rates
    try:
        counts["rates"] = db.execute(text("SELECT COUNT(*) FROM system_rates WHERE is_active = true")).scalar() or 0
    except:
        counts["rates"] = 0
    
    # Notifications unread
    try:
        counts["notifications_unread"] = db.execute(text(
            "SELECT COUNT(*) FROM notifications WHERE is_read = false AND user_id = :uid"
        ), {"uid": current_user.id}).scalar() or 0
    except:
        counts["notifications_unread"] = 0
    
    # Invoices by status
    try:
        counts["invoices_total"] = db.execute(text("SELECT COUNT(*) FROM invoices WHERE is_active = true")).scalar() or 0
        counts["invoices_pending"] = db.execute(text("SELECT COUNT(*) FROM invoices WHERE UPPER(status) = 'PENDING' AND is_active = true")).scalar() or 0
        counts["invoices_paid"] = db.execute(text("SELECT COUNT(*) FROM invoices WHERE UPPER(status) = 'PAID' AND is_active = true")).scalar() or 0
    except:
        counts["invoices_total"] = 0
        counts["invoices_pending"] = 0
        counts["invoices_paid"] = 0
    
    return counts


@router.get("/financial-summary")
async def get_financial_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Financial summary for dashboard: budgets, invoices, costs.
    Scoped by user role/region/area.
    """
    from app.models import Budget
    
    user = db.query(User).options(selectinload(User.role)).filter(User.id == current_user.id).first()
    
    # Base budget query with scope
    budget_q = db.query(Budget).filter(Budget.is_active == True, Budget.project_id != None)
    if user.role and user.role.code == "REGION_MANAGER" and user.region_id:
        budget_q = budget_q.filter(Budget.region_id == user.region_id)
    elif user.role and user.role.code == "AREA_MANAGER" and user.area_id:
        budget_q = budget_q.filter(Budget.area_id == user.area_id)
    
    budgets = budget_q.all()
    
    total_budget = sum(float(b.total_amount or 0) for b in budgets)
    total_committed = sum(float(b.committed_amount or 0) for b in budgets)
    total_spent = sum(float(b.spent_amount or 0) for b in budgets)
    total_remaining = sum(float(b.remaining_amount or 0) for b in budgets)
    
    # Overrun count
    overrun = sum(1 for b in budgets if (b.spent_amount or 0) + (b.committed_amount or 0) > (b.total_amount or 0))
    
    # Invoice stats
    try:
        inv_stats = db.execute(text("""
            SELECT status, COUNT(*) as cnt, COALESCE(SUM(total_amount),0) as total
            FROM invoices WHERE is_active = true
            GROUP BY status
        """)).fetchall()
        invoices = {r.status: {"count": r.cnt, "amount": float(r.total)} for r in inv_stats}
    except:
        invoices = {}
    
    return {
        "budgets": {
            "count": len(budgets),
            "total": round(total_budget, 2),
            "committed": round(total_committed, 2),
            "spent": round(total_spent, 2),
            "remaining": round(total_remaining, 2),
            "utilization_pct": round((total_spent + total_committed) / total_budget * 100, 1) if total_budget > 0 else 0,
            "overrun_count": overrun,
        },
        "invoices": invoices,
        "invoices_total": sum(v["amount"] for v in invoices.values()),
    }


# ============================================
# Missing endpoints called by frontend
# ============================================

@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Alias for /summary — frontend calls /dashboard/stats."""
    return await get_dashboard_summary(db=db, current_user=current_user)


@router.get("/activity")
async def get_dashboard_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Recent activity feed for dashboard."""
    from app.models.activity_log import ActivityLog

    query = db.query(ActivityLog).order_by(desc(ActivityLog.created_at))

    if current_user.role and current_user.role.code not in ("ADMIN", "SYSTEM_ADMIN"):
        query = query.filter(ActivityLog.user_id == current_user.id)

    logs = query.limit(limit).all()

    return [
        {
            "id": log.id,
            "action": log.action if hasattr(log, "action") else getattr(log, "activity_type", None),
            "description": getattr(log, "description", None) or getattr(log, "details", None),
            "entity_type": getattr(log, "entity_type", None),
            "entity_id": getattr(log, "entity_id", None),
            "user_id": log.user_id,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/hours")
async def get_dashboard_hours(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    period: str = "month"
) -> Dict[str, Any]:
    """Work-hours summary for dashboard."""
    from app.models import Worklog

    now = datetime.now()
    if period == "week":
        start = now - timedelta(days=now.weekday())
    elif period == "year":
        start = now.replace(month=1, day=1)
    else:
        start = now.replace(day=1)

    start = start.replace(hour=0, minute=0, second=0, microsecond=0)

    query = db.query(
        func.coalesce(func.sum(Worklog.work_hours), 0).label("total_work_hours"),
        func.coalesce(func.sum(Worklog.break_hours), 0).label("total_break_hours"),
        func.coalesce(func.sum(Worklog.total_hours), 0).label("total_hours"),
        func.count(Worklog.id).label("worklog_count"),
    ).filter(Worklog.report_date >= start.date())

    if current_user.role and current_user.role.code not in ("ADMIN", "SYSTEM_ADMIN"):
        query = query.filter(Worklog.user_id == current_user.id)

    row = query.one()
    return {
        "period": period,
        "start_date": start.date().isoformat(),
        "total_work_hours": float(row.total_work_hours),
        "total_break_hours": float(row.total_break_hours),
        "total_hours": float(row.total_hours),
        "worklog_count": row.worklog_count,
    }


@router.get("/equipment/active")
async def get_dashboard_active_equipment(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Active equipment for dashboard widget."""
    from app.models.equipment import Equipment

    equipment_list = (
        db.query(Equipment)
        .filter(Equipment.status == "in_use", Equipment.is_active == True)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": e.id,
            "name": getattr(e, "name", None) or getattr(e, "description", ""),
            "code": getattr(e, "code", None),
            "status": e.status,
            "supplier_id": getattr(e, "supplier_id", None),
        }
        for e in equipment_list
    ]


@router.get("/suppliers/active")
async def get_dashboard_active_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Active suppliers for dashboard widget."""
    from app.models.supplier import Supplier

    suppliers = (
        db.query(Supplier)
        .filter(Supplier.is_active == True)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": s.id,
            "name": s.name,
            "contact_name": getattr(s, "contact_name", None),
            "phone": getattr(s, "phone", None),
            "is_active": s.is_active,
        }
        for s in suppliers
    ]


@router.get("/monthly-costs")
async def get_monthly_costs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    months: int = 6
) -> List[Dict[str, Any]]:
    """Monthly cost breakdown for dashboard chart."""
    from app.models import Worklog

    user = db.query(User).options(selectinload(User.role)).filter(User.id == current_user.id).first()

    results = []
    now = datetime.now()
    for i in range(months - 1, -1, -1):
        month_date = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        m = month_date.month
        y = month_date.year

        query = db.query(
            func.coalesce(func.sum(Worklog.cost_before_vat), 0).label("cost"),
            func.coalesce(func.sum(Worklog.total_hours), 0).label("hours"),
            func.count(Worklog.id).label("count"),
        ).filter(
            extract('month', Worklog.report_date) == m,
            extract('year', Worklog.report_date) == y,
        )

        if user.role and user.role.code == "REGION_MANAGER" and user.region_id:
            query = query.filter(Worklog.area_id.in_(
                db.query(Area.id).filter(Area.region_id == user.region_id)
            ))
        elif user.role and user.role.code == "AREA_MANAGER" and user.area_id:
            query = query.filter(Worklog.area_id == user.area_id)

        row = query.one()
        results.append({
            "month": f"{y}-{m:02d}",
            "month_name": month_date.strftime("%b"),
            "cost": float(row.cost),
            "hours": float(row.hours),
            "count": row.count,
        })

    return results


@router.get("/region-areas")
async def get_region_areas_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Area breakdown for region manager dashboard."""
    from app.models import Worklog

    user = db.query(User).options(selectinload(User.role)).filter(User.id == current_user.id).first()

    if not user.region_id:
        return []

    areas = db.query(Area).filter(Area.region_id == user.region_id).all()
    result = []
    for area in areas:
        project_count = db.query(func.count(Project.id)).filter(
            Project.area_id == area.id, Project.is_active == True
        ).scalar() or 0

        wo_count = db.query(func.count(WorkOrder.id)).join(
            Project, WorkOrder.project_id == Project.id
        ).filter(
            Project.area_id == area.id,
            WorkOrder.status.in_(["PENDING", "IN_PROGRESS", "PENDING_SUPPLIER"]),
            WorkOrder.is_active == True,
        ).scalar() or 0

        hours = db.query(func.coalesce(func.sum(Worklog.total_hours), 0)).filter(
            Worklog.area_id == area.id,
            extract('month', Worklog.report_date) == datetime.now().month,
            extract('year', Worklog.report_date) == datetime.now().year,
        ).scalar() or 0

        result.append({
            "id": area.id,
            "name": area.name,
            "code": area.code,
            "manager_name": area.manager.full_name if area.manager else None,
            "active_projects": project_count,
            "open_work_orders": wo_count,
            "hours_this_month": float(hours),
        })

    return result


@router.get("/work-manager-summary")
async def get_work_manager_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Weekly summary for WORK_MANAGER dashboard.
    Returns real hours, active work orders, equipment in use.
    """
    now = datetime.now()
    week_ago = now - timedelta(days=7)

    # Hours this week (non-rejected worklogs by this user)
    hours_this_week = db.execute(text("""
        SELECT COALESCE(SUM(w.work_hours), 0)
        FROM worklogs w
        WHERE w.user_id = :uid
          AND UPPER(w.status) != 'REJECTED'
          AND w.is_active = true
          AND w.created_at >= :since
    """), {"uid": current_user.id, "since": week_ago}).scalar() or 0

    # Active work orders created by or assigned to this user
    active_wo = db.execute(text("""
        SELECT COUNT(*)
        FROM work_orders wo
        WHERE wo.created_by_id = :uid
          AND UPPER(wo.status) IN ('APPROVED','APPROVED_AND_SENT','ACTIVE','IN_PROGRESS',
                                    'SUPPLIER_ACCEPTED_PENDING_COORDINATOR')
          AND wo.deleted_at IS NULL
          AND wo.is_active = true
    """), {"uid": current_user.id}).scalar() or 0

    # Equipment in use (from active work orders by this user)
    equipment_in_use = db.execute(text("""
        SELECT COUNT(DISTINCT wo.equipment_id)
        FROM work_orders wo
        WHERE wo.created_by_id = :uid
          AND UPPER(wo.status) IN ('APPROVED','APPROVED_AND_SENT','ACTIVE','IN_PROGRESS',
                                    'SUPPLIER_ACCEPTED_PENDING_COORDINATOR')
          AND wo.equipment_id IS NOT NULL
          AND wo.deleted_at IS NULL
          AND wo.is_active = true
    """), {"uid": current_user.id}).scalar() or 0

    # Hours this month (for context)
    month_start = now.replace(day=1, hour=0, minute=0, second=0)
    hours_this_month = db.execute(text("""
        SELECT COALESCE(SUM(w.work_hours), 0)
        FROM worklogs w
        WHERE w.user_id = :uid
          AND UPPER(w.status) != 'REJECTED'
          AND w.is_active = true
          AND w.created_at >= :since
    """), {"uid": current_user.id, "since": month_start}).scalar() or 0

    # Pending worklogs waiting for approval
    pending_worklogs = db.execute(text("""
        SELECT COUNT(*)
        FROM worklogs w
        WHERE w.user_id = :uid
          AND UPPER(w.status) = 'SUBMITTED'
          AND w.is_active = true
    """), {"uid": current_user.id}).scalar() or 0

    # Approved work orders where equipment not yet scanned
    pending_scan = db.execute(text("""
        SELECT COUNT(*)
        FROM work_orders wo
        WHERE wo.created_by_id = :uid
          AND UPPER(wo.status) = 'APPROVED_AND_SENT'
          AND (wo.equipment_scanned IS NULL OR wo.equipment_scanned = false)
          AND wo.deleted_at IS NULL
          AND wo.is_active = true
    """), {"uid": current_user.id}).scalar() or 0

    # Equipment scanned but worklogs incomplete
    pending_worklogs_fill = db.execute(text("""
        SELECT COUNT(*)
        FROM work_orders wo
        WHERE wo.created_by_id = :uid
          AND UPPER(wo.status) = 'APPROVED_AND_SENT'
          AND wo.equipment_scanned = true
          AND COALESCE(wo.actual_hours, 0) < COALESCE(wo.estimated_hours, 0)
          AND wo.deleted_at IS NULL
          AND wo.is_active = true
    """), {"uid": current_user.id}).scalar() or 0

    # Worklogs submitted pending approval
    submitted_worklogs = db.execute(text("""
        SELECT COUNT(*)
        FROM worklogs w
        WHERE w.user_id = :uid
          AND UPPER(w.status) = 'PENDING_APPROVAL'
          AND w.is_active = true
    """), {"uid": current_user.id}).scalar() or 0

    # Area manager info
    area_manager = None
    if current_user.area_id:
        am_row = db.execute(text("""
            SELECT u.full_name, u.email, u.phone
            FROM users u
            JOIN roles r ON r.id = u.role_id
            WHERE u.area_id = :area_id
              AND r.code = 'AREA_MANAGER'
              AND u.is_active = true
            LIMIT 1
        """), {"area_id": current_user.area_id}).first()
        if am_row:
            area_manager = {
                "name": am_row[0],
                "email": am_row[1],
                "phone": am_row[2],
            }

    return {
        "hours_this_week": float(hours_this_week),
        "hours_this_month": float(hours_this_month),
        "active_work_orders": int(active_wo),
        "equipment_in_use": int(equipment_in_use),
        "pending_worklogs": int(pending_worklogs),
        "pending_scan": int(pending_scan),
        "pending_worklogs_fill": int(pending_worklogs_fill),
        "submitted_worklogs": int(submitted_worklogs),
        "area_manager": area_manager,
    }
