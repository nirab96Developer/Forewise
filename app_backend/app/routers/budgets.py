"""
Budgets Router
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.budget import (
    BudgetCreate, BudgetUpdate, BudgetResponse,
    BudgetList, BudgetSearch, BudgetStatistics
)
from app.services.budget_service import BudgetService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

router = APIRouter(prefix="/budgets", tags=["Budgets"])
budget_service = BudgetService()


@router.get("", response_model=BudgetList)
def list_budgets(
    search: Annotated[BudgetSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List budgets"""
    require_permission(current_user, "budgets.read")
    budgets, total = budget_service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return BudgetList(items=budgets, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


@router.get("/summary")
def get_budget_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Hierarchical budget summary: regions → areas → projects"""
    require_permission(current_user, "budgets.read")
    from app.models import Budget, Project, Region, Area
    try:
        from app.models.location import Location
    except Exception:
        Location = None

    q = db.query(Budget).filter(Budget.is_active == True)

    # Scope by user role so only relevant budgets are loaded
    role_code = getattr(current_user, 'role', None)
    role_code = getattr(role_code, 'code', '') if role_code else ''
    if role_code == 'REGION_MANAGER' and current_user.region_id:
        q = q.filter(Budget.region_id == current_user.region_id)
    elif role_code == 'AREA_MANAGER' and current_user.area_id:
        q = q.filter(Budget.area_id == current_user.area_id)

    budgets = q.all()

    # Pre-load all lookups in single queries to avoid N+1
    all_project_ids = {b.project_id for b in budgets if b.project_id}
    all_area_ids = {b.area_id for b in budgets if b.area_id}

    projects_map = {}
    if all_project_ids:
        for p in db.query(Project).filter(Project.id.in_(all_project_ids)).all():
            projects_map[p.id] = p
            if p.area_id:
                all_area_ids.add(p.area_id)

    areas_map = {}
    all_region_ids = {b.region_id for b in budgets if b.region_id}
    if all_area_ids:
        for a in db.query(Area).filter(Area.id.in_(all_area_ids)).all():
            areas_map[a.id] = a
            if a.region_id:
                all_region_ids.add(a.region_id)

    regions_map = {}
    if all_region_ids:
        for r in db.query(Region).filter(Region.id.in_(all_region_ids)).all():
            regions_map[r.id] = r

    locations_map = {}
    if Location:
        loc_ids = {p.location_id for p in projects_map.values() if p.location_id}
        if loc_ids:
            for loc in db.query(Location).filter(Location.id.in_(loc_ids)).all():
                locations_map[loc.id] = loc

    # Aggregate by region
    region_map: dict = {}
    area_map: dict = {}
    project_rows = []

    for b in budgets:
        total = float(b.total_amount or 0)
        committed = float(b.committed_amount or 0)
        spent = float(b.spent_amount or 0)
        remaining = total - committed - spent
        utilized = committed + spent
        pct = round(utilized / total * 100, 1) if total > 0 else 0

        region_id = b.region_id
        area_id = b.area_id
        project_id = b.project_id
        region_name = None
        area_name = None
        project_name = None
        project_code = None
        forest_name = None

        if project_id:
            proj = projects_map.get(project_id)
            if proj:
                project_name = proj.name
                project_code = proj.code
                area_id = area_id or proj.area_id
                if proj.location_id:
                    loc = locations_map.get(proj.location_id)
                    if loc:
                        forest_name = loc.name

        if area_id:
            area = areas_map.get(area_id)
            if area:
                area_name = area.name
                region_id = region_id or area.region_id

        if region_id:
            reg = regions_map.get(region_id)
            if reg:
                region_name = reg.name

        # Region aggregation
        if region_id:
            if region_id not in region_map:
                region_map[region_id] = {
                    "id": region_id, "name": region_name or f"מרחב {region_id}",
                    "budget_id": b.id if not project_id and not area_id else None,
                    "total_amount": 0.0, "committed_amount": 0.0,
                    "spent_amount": 0.0, "remaining_amount": 0.0,
                }
            rm = region_map[region_id]
            rm["total_amount"] += total
            rm["committed_amount"] += committed
            rm["spent_amount"] += spent
            rm["remaining_amount"] += remaining
            if not project_id and not area_id:
                rm["budget_id"] = b.id

        # Area aggregation
        if area_id:
            if area_id not in area_map:
                area_map[area_id] = {
                    "id": area_id, "name": area_name or f"אזור {area_id}",
                    "region_id": region_id, "region_name": region_name,
                    "budget_id": b.id if not project_id else None,
                    "total_amount": 0.0, "committed_amount": 0.0,
                    "spent_amount": 0.0, "remaining_amount": 0.0,
                }
            am = area_map[area_id]
            am["total_amount"] += total
            am["committed_amount"] += committed
            am["spent_amount"] += spent
            am["remaining_amount"] += remaining
            if not project_id:
                am["budget_id"] = b.id

        # Project row
        if project_id and project_name:
            project_rows.append({
                "id": b.id,
                "project_id": project_id,
                "project_name": project_name,
                "project_code": project_code,
                "forest_name": forest_name,
                "area_id": area_id,
                "area_name": area_name,
                "region_id": region_id,
                "region_name": region_name,
                "total_amount": total,
                "committed_amount": committed,
                "spent_amount": spent,
                "remaining_amount": remaining,
                "utilization_pct": pct,
            })

    # Finalize utilization pct
    regions_out = []
    for rm in region_map.values():
        t = rm["total_amount"]
        u = rm["committed_amount"] + rm["spent_amount"]
        rm["utilization_pct"] = round(u / t * 100, 1) if t > 0 else 0
        regions_out.append(rm)

    areas_out = []
    for am in area_map.values():
        t = am["total_amount"]
        u = am["committed_amount"] + am["spent_amount"]
        am["utilization_pct"] = round(u / t * 100, 1) if t > 0 else 0
        areas_out.append(am)

    return {
        "regions": regions_out,
        "areas": areas_out,
        "projects": project_rows,
    }


@router.get("/statistics", response_model=BudgetStatistics)
def get_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get statistics"""
    require_permission(current_user, "budgets.read")
    return budget_service.get_statistics(db)


@router.get("/by-code/{code}", response_model=BudgetResponse)
def get_by_code(
    code: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get by code"""
    require_permission(current_user, "budgets.read")
    budget = budget_service.get_by_code(db, code)
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Budget '{code}' not found")
    return budget


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get budget"""
    require_permission(current_user, "budgets.read")
    budget = budget_service.get_by_id_or_404(db, budget_id)
    return budget


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    data: BudgetCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create budget"""
    require_permission(current_user, "budgets.create")
    try:
        budget = budget_service.create(db, data, current_user.id)
        return budget
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update budget"""
    require_permission(current_user, "budgets.update")
    from app.core.scope import enforce_scope_for_entity
    existing = budget_service.get_by_id_or_404(db, budget_id)
    enforce_scope_for_entity(current_user, existing, db)
    try:
        budget = budget_service.update(db, budget_id, data, current_user.id)
        return budget
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Delete budget"""
    require_permission(current_user, "budgets.delete")
    from app.core.scope import enforce_scope_for_entity
    existing = budget_service.get_by_id_or_404(db, budget_id)
    enforce_scope_for_entity(current_user, existing, db)
    try:
        budget_service.soft_delete(db, budget_id, current_user.id)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{budget_id}/restore", response_model=BudgetResponse)
def restore_budget(
    budget_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Restore budget"""
    require_permission(current_user, "budgets.restore")
    budget = budget_service.restore(db, budget_id, current_user.id)
    return budget


# ============================================
# BUDGET DETAIL + COMMITTED + SPENT
# ============================================

@router.get("/{budget_id}/detail")
def get_budget_detail(
    budget_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Budget detail with project/region/area info + KPIs."""
    from app.models import Budget, Project, Region, Area
    from sqlalchemy import text
    
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.is_active == True).first()
    if not budget:
        raise HTTPException(status_code=404, detail="תקציב לא נמצא")
    
    # Scope check
    if hasattr(current_user, 'role') and current_user.role:
        if current_user.role.code == "REGION_MANAGER" and current_user.region_id:
            if budget.region_id and budget.region_id != current_user.region_id:
                raise HTTPException(status_code=403, detail="אין הרשאה לתקציב זה")
        elif current_user.role.code == "AREA_MANAGER" and current_user.area_id:
            if budget.area_id and budget.area_id != current_user.area_id:
                raise HTTPException(status_code=403, detail="אין הרשאה לתקציב זה")
    
    project = db.query(Project).filter(Project.id == budget.project_id).first() if budget.project_id else None
    region = db.query(Region).filter(Region.id == budget.region_id).first() if budget.region_id else None
    area = db.query(Area).filter(Area.id == budget.area_id).first() if budget.area_id else None
    
    total = float(budget.total_amount or 0)
    committed = float(budget.committed_amount or 0)
    spent = float(budget.spent_amount or 0)
    remaining = total - committed - spent
    
    # Budget items
    items = []
    try:
        rows = db.execute(text("SELECT id, name, category, allocated_amount, used_amount, locked_amount, remaining_amount FROM budget_items WHERE budget_id = :bid AND is_active = true"), {"bid": budget_id}).fetchall()
        items = [{"id": r.id, "name": r.name, "category": r.category, "allocated": float(r.allocated_amount), "used": float(r.used_amount), "locked": float(r.locked_amount), "remaining": float(r.remaining_amount)} for r in rows]
    except:
        pass
    
    return {
        "id": budget.id,
        "name": budget.name,
        "project_id": budget.project_id,
        "project_name": project.name if project else None,
        "region_id": budget.region_id,
        "region_name": region.name if region else None,
        "area_id": budget.area_id,
        "area_name": area.name if area else None,
        "status": budget.status,
        "fiscal_year": budget.fiscal_year,
        "total_amount": total,
        "committed_amount": committed,
        "spent_amount": spent,
        "remaining_amount": remaining,
        "utilization_pct": round((committed + spent) / total * 100, 1) if total > 0 else 0,
        "items": items,
    }


@router.get("/{budget_id}/committed")
def get_budget_committed(
    budget_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Work Orders holding budget (committed amounts)."""
    from app.models import Budget, WorkOrder, Project, Supplier
    
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.is_active == True).first()
    if not budget or not budget.project_id:
        return {"total": 0, "sum": 0, "items": []}
    
    wos = db.query(WorkOrder).filter(
        WorkOrder.project_id == budget.project_id,
        WorkOrder.status.in_(["PENDING", "SENT", "PENDING_SUPPLIER", "ACCEPTED", "IN_PROGRESS"]),
        WorkOrder.is_active == True,
        WorkOrder.total_amount > 0
    ).all()
    
    # Get supplier names
    sup_ids = set(wo.supplier_id for wo in wos if wo.supplier_id)
    sups = {}
    if sup_ids:
        for s in db.query(Supplier).filter(Supplier.id.in_(sup_ids)).all():
            sups[s.id] = s.name
    
    items = []
    total_sum = 0
    for wo in wos:
        amt = float(wo.total_amount or 0)
        total_sum += amt
        items.append({
            "work_order_id": wo.id,
            "order_number": wo.order_number,
            "title": wo.title,
            "supplier_name": sups.get(wo.supplier_id, "—"),
            "status": wo.status,
            "hourly_rate": float(wo.hourly_rate) if wo.hourly_rate else None,
            "estimated_hours": float(wo.estimated_hours) if wo.estimated_hours else None,
            "committed_amount": amt,
        })
    
    return {"total": len(items), "sum": round(total_sum, 2), "items": items}


@router.get("/{budget_id}/spent")
def get_budget_spent(
    budget_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Worklogs that consumed budget (spent amounts)."""
    from app.models import Budget, Worklog
    from sqlalchemy import text
    
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.is_active == True).first()
    if not budget or not budget.project_id:
        return {"total": 0, "sum": 0, "vat_sum": 0, "items": []}
    
    wls = db.query(Worklog).filter(
        Worklog.project_id == budget.project_id,
        Worklog.is_active == True,
    ).order_by(Worklog.report_date.desc()).all()
    
    items = []
    total_sum = 0
    vat_sum = 0
    for wl in wls:
        amt = float(wl.cost_before_vat or 0)
        vat = float(wl.cost_with_vat or 0) - amt
        total_sum += amt
        vat_sum += vat
        items.append({
            "worklog_id": wl.id,
            "report_date": str(wl.report_date) if wl.report_date else None,
            "work_order_id": wl.work_order_id,
            "status": wl.status,
            "hours": float(wl.work_hours) if hasattr(wl, 'work_hours') and wl.work_hours else float(wl.total_hours) if hasattr(wl, 'total_hours') and wl.total_hours else None,
            "hourly_rate": float(wl.hourly_rate_snapshot) if hasattr(wl, 'hourly_rate_snapshot') and wl.hourly_rate_snapshot else None,
            "amount": amt,
            "vat_amount": round(vat, 2),
            "total_with_vat": float(wl.cost_with_vat) if wl.cost_with_vat else amt,
        })
    
    return {"total": len(items), "sum": round(total_sum, 2), "vat_sum": round(vat_sum, 2), "items": items}
