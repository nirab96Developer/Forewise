"""Dashboard Router"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, and_, or_, desc, extract, text

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.core.authorization import AuthorizationService


# Wave Dashboard — single shared dependency injected on every dashboard
# route. The migration a3b4c5d6e7f8 just removed DASHBOARD.VIEW from
# SUPPLIER, so a supplier hitting any /dashboard/* now gets 403 here
# BEFORE the handler runs its own scope filter. Rationale: the dashboard
# returns merged financial / KPI / activity data; "scope filter to empty"
# is not the same as "permission denied" — we want the latter on principle.
def _dashboard_view(current_user=Depends(get_current_user)):
    require_permission(current_user, "dashboard.view")
    return current_user
from app.models import User, Project, Budget, WorkOrder, Region, Area, Location, Invoice, Supplier

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
    current_user: User = Depends(_dashboard_view)
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
    current_user: User = Depends(_dashboard_view)
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
    
    # Get budget totals (use scoped budget_query for consistency)
    total_budget = budget_query.with_entities(func.sum(Budget.total_amount)).scalar() or 0
    allocated_budget = budget_query.with_entities(func.sum(Budget.allocated_amount)).scalar() or 0
    spent_budget = budget_query.with_entities(func.sum(Budget.spent_amount)).scalar() or 0
    
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
        # After migration d2f3e4a5b6c7 all rows use UPPERCASE status values
        completed_work_orders = db.query(WorkOrder).filter(
            WorkOrder.status == "COMPLETED"
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
    except Exception:
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
        "expired_contracts_count": 0,
        
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

@router.get("/admin-overview")
async def get_admin_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(_dashboard_view)
) -> Dict[str, Any]:
    """Admin dashboard overview — aggregates KPIs, financial, alerts, charts, events."""
    if not current_user.role or current_user.role.code not in ("ADMIN", "SUPER_ADMIN"):
        raise HTTPException(status_code=403, detail="Admin access required")
    from datetime import timedelta
    now = datetime.now()
    week_ago = now - timedelta(days=7)

    db.query(func.count(WorkOrder.id)).filter(WorkOrder.deleted_at.is_(None)).scalar() or 0
    wo_open = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status.in_(['PENDING', 'DISTRIBUTING', 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR', 'APPROVED_AND_SENT']),
        WorkOrder.deleted_at.is_(None)
    ).scalar() or 0
    wo_stuck = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status.in_(['DISTRIBUTING', 'SUPPLIER_ACCEPTED_PENDING_COORDINATOR']),
        WorkOrder.updated_at < now - timedelta(hours=48),
        WorkOrder.deleted_at.is_(None)
    ).scalar() or 0
    wo_expired_week = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status == 'EXPIRED', WorkOrder.updated_at >= week_ago
    ).scalar() or 0

    from app.models.worklog import Worklog
    pending_wl = db.query(func.count(Worklog.id)).filter(
        Worklog.status.in_(['PENDING', 'SUBMITTED']), Worklog.is_active == True
    ).scalar() or 0

    pending_inv = db.query(func.count(Invoice.id)).filter(
        Invoice.status == 'DRAFT', Invoice.deleted_at.is_(None)
    ).scalar() or 0

    budget_query = db.query(Budget)
    total_budget = budget_query.with_entities(func.sum(Budget.total_amount)).scalar() or 0
    committed = budget_query.with_entities(func.sum(Budget.committed_amount)).scalar() or 0
    spent = budget_query.with_entities(func.sum(Budget.spent_amount)).scalar() or 0
    remaining = float(total_budget) - float(committed) - float(spent)
    utilization = (float(spent) / float(total_budget) * 100) if float(total_budget) > 0 else 0
    overrun = db.query(func.count(Budget.id)).filter(
        Budget.spent_amount > Budget.total_amount, Budget.total_amount > 0, Budget.is_active == True
    ).scalar() or 0

    # Alerts
    alerts = []
    if wo_stuck > 0:
        alerts.append({"type": "critical", "message": f"{wo_stuck} הזמנות תקועות מעל 48 שעות", "link": "/work-orders"})
    if overrun > 0:
        alerts.append({"type": "critical", "message": f"{overrun} פרויקטים בחריגת תקציב", "link": "/settings/budgets"})
    if pending_wl > 5:
        alerts.append({"type": "warning", "message": f"{pending_wl} דיווחים ממתינים לאישור", "link": "/accountant-inbox"})
    if pending_inv > 0:
        alerts.append({"type": "info", "message": f"{pending_inv} חשבוניות בטיוטה", "link": "/invoices"})

    # Charts: WO per day last 14 days
    wo_chart = []
    for i in range(13, -1, -1):
        d = (now - timedelta(days=i)).date()
        cnt = db.query(func.count(WorkOrder.id)).filter(
            func.date(WorkOrder.created_at) == d
        ).scalar() or 0
        wo_chart.append({"date": d.isoformat(), "count": cnt})

    wl_chart = []
    for i in range(13, -1, -1):
        d = (now - timedelta(days=i)).date()
        cnt = db.query(func.count(Worklog.id)).filter(
            func.date(Worklog.created_at) == d
        ).scalar() or 0
        wl_chart.append({"date": d.isoformat(), "count": cnt})

    # Recent events
    recent = db.execute(text("""
        SELECT al.id, al.action, al.description, al.entity_type, al.entity_id,
               al.user_id, al.created_at, al.metadata_json,
               u.full_name as user_name
        FROM activity_logs al
        LEFT JOIN users u ON u.id = al.user_id
        ORDER BY al.created_at DESC
        LIMIT 20
    """)).fetchall()
    events = [
        {
            "id": r[0], "action": r[1] or "", "description": r[2] or "",
            "entity_type": r[3] or "", "entity_id": r[4],
            "user_id": r[5], "created_at": r[6].isoformat() if r[6] else "",
            "metadata": r[7], "user_name": r[8]
        }
        for r in recent
    ]

    return {
        "kpis": {
            "open_work_orders": wo_open,
            "stuck_orders": wo_stuck,
            "pending_worklogs": pending_wl,
            "pending_invoices": pending_inv,
            "budget_overrun": overrun,
            "expired_wo_week": wo_expired_week,
            "total_users": db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0,
            "total_suppliers": db.query(func.count(Supplier.id)).filter(Supplier.is_active == True).scalar() or 0,
            "total_projects": db.query(func.count(Project.id)).filter(Project.deleted_at.is_(None)).scalar() or 0,
        },
        "financial": {
            "total": float(total_budget),
            "committed": float(committed),
            "spent": float(spent),
            "remaining": remaining,
            "utilization_pct": round(utilization, 1),
        },
        "alerts": alerts,
        "wo_chart": wo_chart,
        "wl_chart": wl_chart,
        "recent_events": events,
    }


@router.get("/map")
async def get_dashboard_map(
    db: Session = Depends(get_db),
    current_user: User = Depends(_dashboard_view)
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
    current_user: User = Depends(_dashboard_view),
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
    current_user: User = Depends(_dashboard_view),
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
    current_user: User = Depends(_dashboard_view)
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
    current_user: User = Depends(_dashboard_view)
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
    current_user: User = Depends(_dashboard_view)
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
    current_user: User = Depends(_dashboard_view)
) -> Dict[str, Any]:
    """Alias for /summary — frontend calls /dashboard/stats."""
    return await get_dashboard_summary(db=db, current_user=current_user)


@router.get("/activity")
async def get_dashboard_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(_dashboard_view),
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
    current_user: User = Depends(_dashboard_view),
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
    current_user: User = Depends(_dashboard_view),
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
    current_user: User = Depends(_dashboard_view),
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
    current_user: User = Depends(_dashboard_view),
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
    current_user: User = Depends(_dashboard_view),
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
    current_user: User = Depends(_dashboard_view),
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

    # Approved work orders where equipment not yet assigned (equipment_id IS NULL = not scanned)
    pending_scan = db.execute(text("""
        SELECT COUNT(*)
        FROM work_orders wo
        WHERE wo.created_by_id = :uid
          AND UPPER(wo.status) = 'APPROVED_AND_SENT'
          AND wo.equipment_id IS NULL
          AND wo.deleted_at IS NULL
          AND wo.is_active = true
    """), {"uid": current_user.id}).scalar() or 0

    # Equipment assigned but worklogs incomplete (has equipment but hours not filled)
    pending_worklogs_fill = db.execute(text("""
        SELECT COUNT(*)
        FROM work_orders wo
        WHERE wo.created_by_id = :uid
          AND UPPER(wo.status) = 'APPROVED_AND_SENT'
          AND wo.equipment_id IS NOT NULL
          AND COALESCE(wo.actual_hours, 0) < COALESCE(wo.estimated_hours, 1)
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


# ============================================
# WORK MANAGER OVERVIEW — alias for frontend
# ============================================
@router.get("/work-manager-overview")
async def get_work_manager_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(_dashboard_view),
) -> Dict[str, Any]:
    """Alias — frontend calls this name."""
    return await get_work_manager_summary(db=db, current_user=current_user)


# ============================================
# REGION MANAGER DASHBOARD
# ============================================
@router.get("/region-overview")
async def get_region_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(_dashboard_view),
) -> Dict[str, Any]:
    """Region Manager dashboard — scoped to the user's region."""
    rid = current_user.region_id
    region_name = current_user.region.name if current_user.region else "מרחב"
    now = datetime.now()

    projects_q = db.query(Project).filter(Project.region_id == rid, Project.deleted_at.is_(None))
    project_ids = [p.id for p in projects_q.all()]

    total_budget = db.execute(text(
        "SELECT COALESCE(SUM(total_amount),0) FROM budgets WHERE region_id=:rid AND is_active=true AND deleted_at IS NULL"
    ), {"rid": rid}).scalar() or 0
    total_spent = db.execute(text(
        "SELECT COALESCE(SUM(spent_amount),0) FROM budgets WHERE region_id=:rid AND is_active=true AND deleted_at IS NULL"
    ), {"rid": rid}).scalar() or 0
    total_committed = db.execute(text(
        "SELECT COALESCE(SUM(committed_amount),0) FROM budgets WHERE region_id=:rid AND is_active=true AND deleted_at IS NULL"
    ), {"rid": rid}).scalar() or 0

    open_wo = 0
    if project_ids:
        id_list = ",".join(str(i) for i in project_ids)
        open_wo = db.execute(text(f"""
            SELECT COUNT(*) FROM work_orders
            WHERE project_id IN ({id_list})
              AND status IN ('PENDING','DISTRIBUTING','APPROVED_AND_SENT','SUPPLIER_ACCEPTED_PENDING_COORDINATOR')
              AND deleted_at IS NULL
        """)).scalar() or 0

    overrun = db.execute(text(
        "SELECT COUNT(*) FROM budgets WHERE region_id=:rid AND is_active=true AND deleted_at IS NULL AND spent_amount > total_amount AND total_amount > 0"
    ), {"rid": rid}).scalar() or 0

    util_pct = round(float(total_spent) / float(total_budget) * 100, 1) if float(total_budget) > 0 else 0

    areas = []
    area_rows = db.query(Area).filter(Area.region_id == rid, Area.deleted_at.is_(None)).all()
    for a in area_rows:
        a_projects = db.execute(text(
            "SELECT COUNT(*) FROM projects WHERE area_id=:aid AND deleted_at IS NULL"
        ), {"aid": a.id}).scalar() or 0
        a_budget = db.execute(text(
            "SELECT COALESCE(SUM(total_amount),0), COALESCE(SUM(spent_amount),0) FROM budgets WHERE area_id=:aid AND is_active=true AND deleted_at IS NULL"
        ), {"aid": a.id}).first()
        a_total = float(a_budget[0]) if a_budget else 0
        a_spent = float(a_budget[1]) if a_budget else 0
        a_util = round(a_spent / a_total * 100, 1) if a_total > 0 else 0

        a_open_wo = 0
        a_pending_wl = 0
        a_pids = [p.id for p in db.query(Project).filter(Project.area_id == a.id, Project.deleted_at.is_(None)).all()]
        if a_pids:
            id_list = ",".join(str(i) for i in a_pids)
            a_open_wo = db.execute(text(f"SELECT COUNT(*) FROM work_orders WHERE project_id IN ({id_list}) AND status IN ('PENDING','DISTRIBUTING','APPROVED_AND_SENT') AND deleted_at IS NULL")).scalar() or 0
            a_pending_wl = db.execute(text(f"SELECT COUNT(*) FROM worklogs WHERE project_id IN ({id_list}) AND UPPER(status)='SUBMITTED' AND is_active=true")).scalar() or 0

        mgr_name = None
        if a.manager_id:
            mgr = db.query(User).filter(User.id == a.manager_id).first()
            mgr_name = mgr.full_name if mgr else None

        areas.append({
            "id": a.id, "name": a.name, "manager_name": mgr_name,
            "projects": a_projects, "budget_total": a_total,
            "utilization_pct": a_util, "open_work_orders": a_open_wo,
            "pending_worklogs": a_pending_wl,
        })

    wo_trend = []
    for d in range(13, -1, -1):
        day = (now - timedelta(days=d)).date()
        if project_ids:
            id_list = ",".join(str(i) for i in project_ids)
            cnt = db.execute(text(f"SELECT COUNT(*) FROM work_orders WHERE project_id IN ({id_list}) AND DATE(created_at)=:day AND deleted_at IS NULL"), {"day": str(day)}).scalar() or 0
        else:
            cnt = 0
        wo_trend.append({"date": str(day), "count": cnt})

    alerts = []
    if overrun > 0:
        alerts.append({"type": "error", "message": f"{overrun} תקציבים בחריגה", "link": "/settings/budgets"})

    return {
        "region_name": region_name,
        "kpis": {
            "total_budget": float(total_budget), "total_spent": float(total_spent),
            "total_committed": float(total_committed), "utilization_pct": util_pct,
            "open_work_orders": open_wo, "overrun_areas": overrun,
        },
        "areas": areas,
        "wo_trend": wo_trend,
        "alerts": alerts,
    }


# ============================================
# AREA MANAGER DASHBOARD
# ============================================
@router.get("/area-overview")
async def get_area_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(_dashboard_view),
) -> Dict[str, Any]:
    """Area Manager dashboard — scoped to the user's area."""
    aid = current_user.area_id
    area_name = current_user.area.name if current_user.area else "אזור"
    now = datetime.now()

    projects = db.query(Project).filter(Project.area_id == aid, Project.deleted_at.is_(None)).all()
    project_ids = [p.id for p in projects]

    open_wo = 0
    stuck_wo = 0
    pending_approval = 0
    draft_inv = 0
    if project_ids:
        id_list = ",".join(str(i) for i in project_ids)
        open_wo = db.execute(text(f"SELECT COUNT(*) FROM work_orders WHERE project_id IN ({id_list}) AND status IN ('PENDING','DISTRIBUTING','APPROVED_AND_SENT','SUPPLIER_ACCEPTED_PENDING_COORDINATOR') AND deleted_at IS NULL")).scalar() or 0
        stuck_wo = db.execute(text(f"SELECT COUNT(*) FROM work_orders WHERE project_id IN ({id_list}) AND status IN ('DISTRIBUTING','SUPPLIER_ACCEPTED_PENDING_COORDINATOR') AND updated_at < :cutoff AND deleted_at IS NULL"), {"cutoff": now - timedelta(hours=48)}).scalar() or 0
        pending_approval = db.execute(text(f"SELECT COUNT(*) FROM worklogs WHERE project_id IN ({id_list}) AND UPPER(status)='SUBMITTED' AND is_active=true")).scalar() or 0
        draft_inv = db.execute(text(f"SELECT COUNT(*) FROM invoices WHERE project_id IN ({id_list}) AND UPPER(status)='DRAFT' AND is_active=true")).scalar() or 0

    budget_row = db.execute(text(
        "SELECT COALESCE(SUM(total_amount),0), COALESCE(SUM(spent_amount),0), COALESCE(SUM(committed_amount),0) FROM budgets WHERE area_id=:aid AND is_active=true AND deleted_at IS NULL"
    ), {"aid": aid}).first()
    b_total = float(budget_row[0]) if budget_row else 0
    b_spent = float(budget_row[1]) if budget_row else 0
    b_committed = float(budget_row[2]) if budget_row else 0
    b_remaining = b_total - b_spent - b_committed
    b_util = round(b_spent / b_total * 100, 1) if b_total > 0 else 0

    wo_list = []
    if project_ids:
        id_list = ",".join(str(i) for i in project_ids)
        rows = db.execute(text(f"""
            SELECT wo.id, wo.order_number, wo.title, wo.status, p.name as project_name,
                   s.name as supplier_name
            FROM work_orders wo
            LEFT JOIN projects p ON p.id = wo.project_id
            LEFT JOIN suppliers s ON s.id = wo.supplier_id
            WHERE wo.project_id IN ({id_list})
              AND wo.status IN ('PENDING','DISTRIBUTING','APPROVED_AND_SENT','SUPPLIER_ACCEPTED_PENDING_COORDINATOR','ACTIVE')
              AND wo.deleted_at IS NULL
            ORDER BY wo.created_at DESC LIMIT 10
        """)).fetchall()
        for r in rows:
            wo_list.append({"id": r[0], "order_number": r[1], "title": r[2], "status": r[3], "project_name": r[4], "supplier_name": r[5]})

    pending_list = []
    if project_ids:
        id_list = ",".join(str(i) for i in project_ids)
        rows = db.execute(text(f"""
            SELECT wl.id, wl.report_number, wl.report_date, wl.work_hours,
                   wl.cost_with_vat, wl.is_overnight, u.full_name as reporter
            FROM worklogs wl
            LEFT JOIN users u ON u.id = wl.user_id
            WHERE wl.project_id IN ({id_list})
              AND UPPER(wl.status) = 'SUBMITTED' AND wl.is_active = true
            ORDER BY wl.created_at DESC LIMIT 10
        """)).fetchall()
        for r in rows:
            pending_list.append({"id": r[0], "report_number": r[1], "report_date": str(r[2]) if r[2] else None, "work_hours": float(r[3] or 0), "cost_with_vat": float(r[4] or 0), "is_overnight": bool(r[5]), "reporter": r[6]})

    alerts = []
    if stuck_wo > 0:
        alerts.append({"type": "warning", "message": f"{stuck_wo} הזמנות תקועות מעל 48 שעות", "link": "/work-orders"})

    return {
        "area_name": area_name,
        "kpis": {
            "open_work_orders": open_wo, "stuck_work_orders": stuck_wo,
            "submitted_for_approval": pending_approval, "draft_invoices": draft_inv,
            "total_projects": len(project_ids),
        },
        "budget": {
            "total": b_total, "spent": b_spent, "committed": b_committed,
            "remaining": b_remaining, "utilization_pct": b_util,
        },
        "work_orders": wo_list,
        "pending_approvals": pending_list,
        "alerts": alerts,
    }


# ============================================
# ORDER COORDINATOR QUEUE
# ============================================
@router.get("/coordinator-queue")
async def get_coordinator_queue(
    status_filter: str = "",
    project_id: str = "",
    search: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(_dashboard_view),
) -> Dict[str, Any]:
    """Order coordinator work order queue with filters."""
    base_filter = "wo.deleted_at IS NULL AND wo.is_active = true"
    params: dict = {}
    role_code = getattr(getattr(current_user, "role", None), "code", None) or ""

    if role_code == "ORDER_COORDINATOR" and getattr(current_user, "region_id", None):
        base_filter += " AND p.region_id = :coord_region_id"
        params["coord_region_id"] = current_user.region_id

    if status_filter:
        base_filter += " AND UPPER(wo.status) = :sf"
        params["sf"] = status_filter.upper()
    if project_id:
        base_filter += " AND wo.project_id = :pid"
        params["pid"] = int(project_id)
    if search:
        base_filter += " AND (wo.order_number ILIKE :q OR wo.title ILIKE :q)"
        params["q"] = f"%{search}%"

    rows = db.execute(text(f"""
        SELECT wo.id, wo.order_number, wo.title, wo.status, wo.priority,
               p.name as project_name, s.name as supplier_name,
               wo.created_at, wo.updated_at, wo.equipment_license_plate,
               wo.project_id, wo.supplier_id, wo.equipment_type,
               wo.is_forced_selection, wo.constraint_notes, wo.portal_expiry,
               u.full_name as creator_name
        FROM work_orders wo
        LEFT JOIN projects  p ON p.id = wo.project_id
        LEFT JOIN suppliers s ON s.id = wo.supplier_id
        LEFT JOIN users     u ON u.id = wo.created_by_id
        WHERE {base_filter}
        ORDER BY
            CASE WHEN UPPER(wo.status) IN ('PENDING','EXPIRED') THEN 0 ELSE 1 END,
            wo.created_at DESC
        LIMIT 50
    """), params).fetchall()

    work_orders = []
    now_ts = datetime.now()
    for r in rows:
        wo_id = r[0]
        # Supplier history with all fields the FE expects
        history = []
        hist_rows = db.execute(text("""
            SELECT si.status, si.sent_at, si.responded_at, si.response_notes,
                   si.decline_reason, s.name as supplier_name
            FROM supplier_invitations si
            LEFT JOIN suppliers s ON s.id = si.supplier_id
            WHERE si.work_order_id = :wid
            ORDER BY si.created_at DESC
        """), {"wid": wo_id}).fetchall()
        for h in hist_rows:
            history.append({
                "supplier_name":  h[5],
                "status":         h[0],
                "sent_at":        str(h[1]) if h[1] else None,
                "responded_at":   str(h[2]) if h[2] else None,
                "notes":          h[3],
                "decline_reason": h[4],
            })

        portal_expiry = r[15]
        # Treat <30min remaining as "expiring soon"
        is_expired_soon = bool(
            portal_expiry
            and portal_expiry > now_ts
            and (portal_expiry - now_ts).total_seconds() < 30 * 60
        )

        work_orders.append({
            "id":               wo_id,
            "order_number":     r[1],
            "title":            r[2],
            "status":           r[3],
            "priority":         r[4],
            "project_name":     r[5],
            "supplier_name":    r[6],
            "created_at":       str(r[7]) if r[7] else None,
            "updated_at":       str(r[8]) if r[8] else None,
            # FE field name: equipment_plate (kept "license_plate" too for backwards compat)
            "license_plate":    r[9],
            "equipment_plate":  r[9],
            "project_id":       r[10],
            "supplier_id":      r[11],
            "equipment_type":   r[12],
            "is_forced":        bool(r[13]),
            "constraint_notes": r[14],
            "is_expired_soon":  is_expired_soon,
            "creator_name":     r[16] or "",
            "supplier_history": history,
        })

    kpi_filter = "wo.deleted_at IS NULL AND wo.is_active=true"
    if role_code == "ORDER_COORDINATOR" and getattr(current_user, "region_id", None):
        kpi_filter += " AND p.region_id = :coord_region_id"

    pending = db.execute(text(f"SELECT COUNT(*) FROM work_orders wo LEFT JOIN projects p ON p.id = wo.project_id WHERE {kpi_filter} AND UPPER(wo.status)='PENDING'"), params).scalar() or 0
    distributing = db.execute(text(f"SELECT COUNT(*) FROM work_orders wo LEFT JOIN projects p ON p.id = wo.project_id WHERE {kpi_filter} AND UPPER(wo.status)='DISTRIBUTING'"), params).scalar() or 0
    supplier_accepted = db.execute(text(f"SELECT COUNT(*) FROM work_orders wo LEFT JOIN projects p ON p.id = wo.project_id WHERE {kpi_filter} AND UPPER(wo.status)='SUPPLIER_ACCEPTED_PENDING_COORDINATOR'"), params).scalar() or 0
    expired = db.execute(text(f"SELECT COUNT(*) FROM work_orders wo LEFT JOIN projects p ON p.id = wo.project_id WHERE {kpi_filter} AND UPPER(wo.status)='EXPIRED'"), params).scalar() or 0
    forced = db.execute(text(f"SELECT COUNT(*) FROM work_orders wo LEFT JOIN projects p ON p.id = wo.project_id WHERE {kpi_filter} AND wo.is_forced_selection=true AND UPPER(wo.status) NOT IN ('COMPLETED','CANCELLED','REJECTED')"), params).scalar() or 0

    project_rows = db.execute(text(f"SELECT DISTINCT p.id, p.name FROM projects p JOIN work_orders wo ON wo.project_id=p.id WHERE {kpi_filter} ORDER BY p.name"), params).fetchall()
    status_options = [
        {"value": "PENDING", "label": "ממתין לשליחה"},
        {"value": "DISTRIBUTING", "label": "בהפצה"},
        {"value": "SUPPLIER_ACCEPTED_PENDING_COORDINATOR", "label": "ספק אישר"},
        {"value": "APPROVED_AND_SENT", "label": "אושר ונשלח"},
        {"value": "EXPIRED", "label": "פג תוקף"},
        {"value": "REJECTED", "label": "נדחה"},
    ]

    alerts = []
    if expired > 0:
        alerts.append({"type": "warning", "message": f"{expired} הזמנות פגות תוקף"})
    if forced > 0:
        alerts.append({"type": "info", "message": f"{forced} הזמנות באילוץ ספק"})

    return {
        "work_orders": work_orders,
        "kpis": {
            "pending": pending, "distributing": distributing,
            "supplier_accepted": supplier_accepted, "expired": expired,
            "forced_cases": forced,
        },
        "alerts": alerts,
        "filter_options": {
            "projects": [{"id": r[0], "name": r[1]} for r in project_rows],
            "statuses": status_options,
        },
    }


# ============================================
# ACCOUNTANT OVERVIEW
# ============================================
@router.get("/accountant-overview")
async def get_accountant_overview(
    status_filter: str = "SUBMITTED",
    project_id: str = "",
    supplier_id: str = "",
    search: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(_dashboard_view),
) -> Dict[str, Any]:
    """Accountant dashboard — worklogs for review, KPIs, filters.

    Phase 3 Wave 2.2.b — closes leak D2 (PHASE3_WAVE22_RECON.md):
    before this commit, any caller with `dashboard.view` (i.e. every
    authenticated non-supplier user) could pull system-wide
    financial KPIs (`pending_amount`, `monthly_approved`, draft
    invoice totals) and a list of worklogs with cost fields. The
    only intended audience is finance — ACCOUNTANT plus ADMINs.

    Role gate (no scope narrowing — ACCOUNTANT is a global role by
    design; cross-region financial visibility is intentional):
      ✅ ACCOUNTANT, ADMIN, SUPER_ADMIN
      ❌ everyone else (403)

    ORDER_COORDINATOR is NOT included — they have their own queue
    via /dashboard/coordinator-queue. If product later wants
    coordinator visibility into financials, that's a deliberate
    addition.
    """
    role_code = (current_user.role.code if current_user.role else "").upper()
    if role_code not in ("ACCOUNTANT", "ADMIN", "SUPER_ADMIN"):
        raise HTTPException(
            status_code=403,
            detail="Accountant dashboard access required",
        )

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    pending_reports = db.execute(text("SELECT COUNT(*) FROM worklogs WHERE UPPER(status)='SUBMITTED' AND is_active=true")).scalar() or 0
    approved_today = db.execute(text("SELECT COUNT(*) FROM worklogs WHERE UPPER(status)='APPROVED' AND is_active=true AND approved_at >= :td"), {"td": today_start}).scalar() or 0
    monthly_approved = db.execute(text("SELECT COALESCE(SUM(cost_with_vat),0) FROM worklogs WHERE UPPER(status)='APPROVED' AND is_active=true AND approved_at >= :ms"), {"ms": month_start}).scalar() or 0
    pending_amount = db.execute(text("SELECT COALESCE(SUM(cost_with_vat),0) FROM worklogs WHERE UPPER(status)='SUBMITTED' AND is_active=true")).scalar() or 0
    draft_invoices = db.execute(text("SELECT COUNT(*) FROM invoices WHERE UPPER(status)='DRAFT' AND is_active=true")).scalar() or 0
    anomalies = db.execute(text("SELECT COUNT(*) FROM worklogs WHERE UPPER(status)='SUBMITTED' AND is_active=true AND (hourly_rate_snapshot IS NULL OR hourly_rate_snapshot <= 0 OR work_hours > 12)")).scalar() or 0

    base_filter = "wl.is_active = true"
    params: dict = {}
    if status_filter:
        base_filter += " AND UPPER(wl.status) = :sf"
        params["sf"] = status_filter.upper()
    if project_id:
        base_filter += " AND wl.project_id = :pid"
        params["pid"] = int(project_id)
    if supplier_id:
        base_filter += " AND wl.supplier_id = :sid"
        params["sid"] = int(supplier_id)
    if search:
        base_filter += " AND (CAST(wl.report_number AS TEXT) ILIKE :q OR u.full_name ILIKE :q)"
        params["q"] = f"%{search}%"

    rows = db.execute(text(f"""
        SELECT wl.id, wl.report_number, wl.report_date, wl.work_hours, wl.cost_with_vat,
               wl.status, wl.is_overnight, wl.hourly_rate_snapshot,
               p.name as project_name, s.name as supplier_name, u.full_name as reporter_name,
               wl.project_id, wl.supplier_id
        FROM worklogs wl
        LEFT JOIN projects p ON p.id = wl.project_id
        LEFT JOIN suppliers s ON s.id = wl.supplier_id
        LEFT JOIN users u ON u.id = wl.user_id
        WHERE {base_filter}
        ORDER BY wl.created_at DESC LIMIT 50
    """), params).fetchall()

    worklogs = []
    for r in rows:
        flags = []
        if not r[7] or float(r[7]) <= 0:
            flags.append("no_rate")
        if r[3] and float(r[3]) > 12:
            flags.append("high_hours")
        if r[3] and float(r[3]) < 1:
            flags.append("low_hours")
        worklogs.append({
            "id": r[0], "report_number": r[1], "report_date": str(r[2]) if r[2] else None,
            "work_hours": float(r[3] or 0), "cost_with_vat": float(r[4] or 0),
            "status": r[5], "is_overnight": bool(r[6]),
            "project_name": r[8], "supplier_name": r[9], "reporter_name": r[10],
            "project_id": r[11], "supplier_id": r[12],
            "flags": flags,
        })

    project_options = db.execute(text("SELECT DISTINCT p.id, p.name FROM projects p JOIN worklogs wl ON wl.project_id=p.id WHERE wl.is_active=true ORDER BY p.name")).fetchall()
    supplier_options = db.execute(text("SELECT DISTINCT s.id, s.name FROM suppliers s JOIN worklogs wl ON wl.supplier_id=s.id WHERE wl.is_active=true ORDER BY s.name")).fetchall()

    return {
        "kpis": {
            "pending_reports": pending_reports, "approved_today": approved_today,
            "monthly_approved": float(monthly_approved), "pending_amount": float(pending_amount),
            "draft_invoices": draft_invoices, "anomalies": anomalies,
        },
        "worklogs": worklogs,
        "filter_options": {
            "projects": [{"id": r[0], "name": r[1]} for r in project_options],
            "suppliers": [{"id": r[0], "name": r[1]} for r in supplier_options],
            "statuses": ["SUBMITTED", "APPROVED", "REJECTED", "PENDING", "DRAFT"],
        },
    }


@router.get("/worklog-detail/{worklog_id}")
async def get_worklog_detail(
    worklog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_dashboard_view),
) -> Dict[str, Any]:
    """Detailed worklog view for accountant modal.

    Phase 3 Wave 2.2.a — closes leak D1 (PHASE3_WAVE22_RECON.md):
    before this commit, any caller with `dashboard.view` could fetch
    any worklog's financials (hourly_rate, cost_with_vat, audit
    trail, supplier name) by guessing the ID. Same shape as the
    Worklog PDF leak closed in Wave 3.1.6.a — `WorklogScopeStrategy`
    already exists; this just wires it.

    Behavior matrix (unchanged for legitimate callers):
      ADMIN / SUPER_ADMIN / ACCOUNTANT → all worklogs (intended UX).
      REGION_MANAGER → worklogs in their region.
      AREA_MANAGER   → worklogs in their area.
      WORK_MANAGER   → worklogs on assigned projects.
      SUPPLIER / FIELD_WORKER (hypothetical) → blocked at the
        `dashboard.view` gate before reaching here, but the strategy
        adds belt-and-braces (OWN_ONLY branch).
    """
    from app.models.worklog import Worklog

    worklog = db.query(Worklog).filter(Worklog.id == worklog_id).first()
    if not worklog:
        raise HTTPException(status_code=404, detail="Worklog not found")

    AuthorizationService(db).authorize(
        current_user,
        resource=worklog,
        resource_type="Worklog",
    )

    row = db.execute(text("""
        SELECT wl.id, wl.report_number, wl.report_date, wl.report_type, wl.status,
               wl.work_hours, wl.break_hours, wl.net_hours, wl.total_hours,
               wl.hourly_rate_snapshot, wl.rate_source_name, wl.cost_before_vat, wl.cost_with_vat,
               wl.is_overnight, wl.overnight_nights, wl.overnight_rate, wl.overnight_total,
               wl.equipment_scanned, wl.equipment_type, wl.notes,
               wl.approved_at, wl.vat_rate,
               p.name as project_name, s.name as supplier_name, u.full_name as reporter_name,
               ap.full_name as approver_name,
               e.license_plate, e.name as equipment_name, e.code as equipment_code,
               wo.order_number as work_order_number
        FROM worklogs wl
        LEFT JOIN projects p ON p.id = wl.project_id
        LEFT JOIN suppliers s ON s.id = wl.supplier_id
        LEFT JOIN users u ON u.id = wl.user_id
        LEFT JOIN users ap ON ap.id = wl.approved_by_user_id
        LEFT JOIN equipment e ON e.id = wl.equipment_id
        LEFT JOIN work_orders wo ON wo.id = wl.work_order_id
        WHERE wl.id = :wid
    """), {"wid": worklog_id}).first()

    if not row:
        # Defensive — should not happen since we already fetched the
        # worklog via ORM above. Kept for parity with the original
        # error path.
        raise HTTPException(status_code=404, detail="Worklog not found")

    warnings = []
    if not row[9] or float(row[9]) <= 0:
        warnings.append("לא נמצא תעריף תקין — ייתכן שהעלות אינה מדויקת")
    if row[5] and float(row[5]) > 10:
        warnings.append(f"שעות עבודה חריגות ({float(row[5]):.1f} שעות)")

    audit_trail = []
    audit_rows = db.execute(text("""
        SELECT al.description, al.created_at, u.full_name
        FROM activity_logs al
        LEFT JOIN users u ON u.id = al.user_id
        WHERE al.entity_type = 'worklog' AND al.entity_id = :wid
        ORDER BY al.created_at DESC LIMIT 20
    """), {"wid": worklog_id}).fetchall()
    for ar in audit_rows:
        audit_trail.append({"description": ar[0], "created_at": str(ar[1]) if ar[1] else None, "user_name": ar[2]})

    inv_row = db.execute(text("""
        SELECT i.invoice_number, i.status FROM invoice_items ii
        JOIN invoices i ON i.id = ii.invoice_id
        WHERE ii.worklog_id = :wid LIMIT 1
    """), {"wid": worklog_id}).first()
    invoice = {"invoice_number": inv_row[0], "status": inv_row[1]} if inv_row else None

    return {
        "id": row[0], "report_number": row[1], "report_date": str(row[2]) if row[2] else None,
        "report_type": row[3], "status": row[4],
        "work_hours": float(row[5] or 0), "break_hours": float(row[6] or 0),
        "net_hours": float(row[7] or row[5] or 0), "total_hours": float(row[8] or 0),
        "hourly_rate": float(row[9] or 0), "rate_source_name": row[10],
        "cost_before_vat": float(row[11] or 0), "cost_with_vat": float(row[12] or 0),
        "is_overnight": bool(row[13]), "overnight_nights": int(row[14] or 0),
        "overnight_rate": float(row[15] or 0), "overnight_total": float(row[16] or 0),
        "equipment_scanned": bool(row[17]), "equipment_type": row[18], "notes": row[19],
        "approved_at": str(row[20]) if row[20] else None, "vat_rate": float(row[21] or 0.18),
        "project_name": row[22], "supplier_name": row[23], "reporter_name": row[24],
        "approver_name": row[25],
        "license_plate": row[26], "equipment_name": row[27], "equipment_code": row[28],
        "work_order_number": row[29],
        "warnings": warnings, "audit_trail": audit_trail, "invoice": invoice,
    }
