"""
Projects Router
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectList, ProjectSearch, ProjectStatistics
)
from app.services.project_service import ProjectService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

router = APIRouter(prefix="/projects", tags=["Projects"])
service = ProjectService()


@router.get("", response_model=ProjectList)
def list_projects(
    search: Annotated[ProjectSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    my_projects: bool = False,
):
    """List projects filtered by the caller's role scope."""
    require_permission(current_user, "projects.read")

    # ── Role-based scope filtering ──────────────────────────────────────────
    role_code = current_user.role.code if current_user.role else ""

    if role_code in ("ADMIN", "ORDER_COORDINATOR"):
        # Full access — no extra filtering
        pass

    elif role_code == "REGION_MANAGER":
        # Restrict to own region (unless caller already narrowed further)
        if search.region_id is None and current_user.region_id:
            search.region_id = current_user.region_id

    elif role_code == "AREA_MANAGER":
        # Restrict to own area
        if search.area_id is None and current_user.area_id:
            search.area_id = current_user.area_id
        elif search.region_id is None and current_user.region_id:
            search.region_id = current_user.region_id

    elif role_code == "ACCOUNTANT":
        # Area-level if area is set, otherwise region-level
        if search.area_id is None and current_user.area_id:
            search.area_id = current_user.area_id
        elif search.region_id is None and current_user.region_id:
            search.region_id = current_user.region_id

    elif role_code == "WORK_MANAGER":
        # Always show only assigned projects
        my_projects = True
    # ────────────────────────────────────────────────────────────────────────

    items, total = service.list(db, search)

    if my_projects:
        from app.models.project_assignment import ProjectAssignment
        assigned_ids = {
            a.project_id for a in db.query(ProjectAssignment.project_id).filter(
                ProjectAssignment.user_id == current_user.id,
                ProjectAssignment.is_active == True,
            ).all()
        }
        items = [p for p in items if p.id in assigned_ids]
        total = len(items)

    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1

    # Enrich items with budget total so frontend can determine active vs. planning
    from sqlalchemy import text as sa_text
    if items:
        ids = [p.id for p in items]
        budget_rows = db.execute(sa_text(
            "SELECT project_id, COALESCE(total_amount,0) FROM budgets "
            "WHERE project_id = ANY(:ids) AND is_active=true AND deleted_at IS NULL"
        ), {"ids": ids}).fetchall()
        budget_map = {r[0]: float(r[1]) for r in budget_rows}
        for p in items:
            p.__dict__['allocated_budget'] = budget_map.get(p.id, 0.0)

    return ProjectList(items=items, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


@router.get("/statistics", response_model=ProjectStatistics)
def get_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get statistics"""
    require_permission(current_user, "projects.read")
    return service.get_statistics(db)


@router.get("/by-code/{code}", response_model=ProjectResponse)
def get_by_code(
    code: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get by code"""
    require_permission(current_user, "projects.read")
    item = service.get_by_code(db, code)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{code}' not found")
    return item


# Alias for frontend compatibility
@router.get("/code/{code}")
def get_by_code_alias(
    code: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get by code - enriched with budget data for Workspace."""
    require_permission(current_user, "projects.read")
    item = service.get_by_code(db, code)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{code}' not found")
    
    # Enrich with budget data
    from app.models import Budget
    from sqlalchemy import text as sa_text
    
    result = {}
    # Copy basic fields — skip geometry/binary types that aren't JSON serializable
    from datetime import datetime, date
    _geo_types = set()
    try:
        from geoalchemy2 import WKBElement
        _geo_types.add(WKBElement)
    except ImportError:
        pass

    for col in item.__table__.columns:
        val = getattr(item, col.name, None)
        if val is None:
            continue
        if _geo_types and isinstance(val, tuple(_geo_types)):
            continue  # skip PostGIS geometry columns
        if isinstance(val, datetime):
            result[col.name] = val.isoformat()
        elif isinstance(val, date):
            result[col.name] = val.isoformat()
        else:
            try:
                import json as _json
                _json.dumps(val)  # test serializability
                result[col.name] = val
            except (TypeError, ValueError):
                result[col.name] = str(val)
    
    # Add relationships — nested objects + flat name aliases for frontend
    if item.region:
        result["region"] = {"id": item.region.id, "name": item.region.name}
        result["region_name"] = item.region.name
    if item.area:
        result["area"] = {"id": item.area.id, "name": item.area.name}
        result["area_name"] = item.area.name

    # Manager = WORK_MANAGER assigned to this project via project_assignments (raw SQL)
    try:
        wm_row = db.execute(
            sa_text("""
                SELECT u.id, u.full_name
                FROM project_assignments pa
                JOIN users u ON u.id = pa.user_id
                JOIN roles r ON r.id = u.role_id
                WHERE pa.project_id = :pid
                  AND pa.is_active = TRUE
                  AND r.code = 'WORK_MANAGER'
                LIMIT 1
            """),
            {"pid": item.id},
        ).fetchone()
    except Exception as _wm_err:
        import logging as _log
        _log.getLogger("app").error(f"[get_by_code] manager query failed: {type(_wm_err).__name__}: {_wm_err}", exc_info=True)
        wm_row = None
    if wm_row:
        result["manager"] = {"id": wm_row[0], "full_name": wm_row[1]}
        result["manager_name"] = wm_row[1]
    else:
        result["manager"] = None
        result["manager_name"] = None

    # Accountant = ACCOUNTANT user in the same area (raw SQL)
    try:
        acc_row = db.execute(
            sa_text("""
                SELECT u.id, u.full_name
                FROM users u
                JOIN roles r ON r.id = u.role_id
                WHERE r.code = 'ACCOUNTANT'
                  AND u.area_id = :area_id
                  AND u.is_active = TRUE
                LIMIT 1
            """),
            {"area_id": item.area_id},
        ).fetchone()
    except Exception as _acc_err:
        import logging as _log
        _log.getLogger("app").error(f"[get_by_code] accountant query failed: {type(_acc_err).__name__}: {_acc_err}", exc_info=True)
        acc_row = None
    if acc_row:
        result["accountant"] = {"id": acc_row[0], "full_name": acc_row[1]}
    else:
        result["accountant"] = None

    # Area manager = AREA_MANAGER in the same area (raw SQL)
    try:
        am_row = db.execute(
            sa_text("""
                SELECT u.id, u.full_name
                FROM users u
                JOIN roles r ON r.id = u.role_id
                WHERE r.code = 'AREA_MANAGER'
                  AND u.area_id = :area_id
                  AND u.is_active = TRUE
                LIMIT 1
            """),
            {"area_id": item.area_id},
        ).fetchone()
    except Exception as _am_err:
        import logging as _log
        _log.getLogger("app").error(f"[get_by_code] area_manager query failed: {type(_am_err).__name__}: {_am_err}", exc_info=True)
        am_row = None
    if am_row:
        result["area_manager"] = {"id": am_row[0], "full_name": am_row[1]}
    else:
        result["area_manager"] = None


    # Add budget info
    budget = db.query(Budget).filter(Budget.project_id == item.id, Budget.is_active == True).first()
    if budget:
        result["allocated_budget"] = float(budget.total_amount or 0)
        result["spent_budget"] = float(budget.spent_amount or 0)
        result["committed_budget"] = float(budget.committed_amount or 0)
        result["budget_status"] = budget.status
    else:
        result["allocated_budget"] = 0
        result["spent_budget"] = 0
        result["committed_budget"] = 0
    
    # Add geo
    coords = _get_project_coordinates(db, [item.id])
    if item.id in coords:
        result["latitude"] = coords[item.id]["latitude"]
        result["longitude"] = coords[item.id]["longitude"]
    
    return result


@router.get("/{item_id}", response_model=ProjectResponse)
def get_project(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get project"""
    require_permission(current_user, "projects.read")
    item = service.get_by_id_or_404(db, item_id)
    return item


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create project"""
    require_permission(current_user, "projects.create")
    try:
        item = service.create(db, data, current_user.id)
        return item
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{item_id}", response_model=ProjectResponse)
def update_project(
    item_id: int,
    data: ProjectUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update project"""
    require_permission(current_user, "projects.update")
    try:
        item = service.update(db, item_id, data, current_user.id)
        return item
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Soft delete project"""
    require_permission(current_user, "projects.delete")
    try:
        service.soft_delete(db, item_id, current_user.id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{item_id}/restore", response_model=ProjectResponse)
def restore_project(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Restore project"""
    require_permission(current_user, "projects.restore")
    item = service.restore(db, item_id, current_user.id)
    return item


# ========================================
# Forest Map Endpoints
# ========================================
from app.services.forest_map_service import forest_map_service
from app.schemas.forest_map import ForestMapResponse


@router.get("/{item_id}/forest-map", response_model=ForestMapResponse)
def get_project_forest_map(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get forest map data for a project
    Returns project location point and forest polygon (if available)
    """
    require_permission(current_user, "projects.read")
    return forest_map_service.get_project_forest_map(db, item_id)


# ============================================
# HELPER: Enrich projects with lat/lng from PostGIS
# ============================================
_geo_cache = {}

def _get_project_coordinates(db, project_ids):
    """Get lat/lng for projects — PostGIS location_geom first, then locations table fallback."""
    if not project_ids:
        return {}
    from sqlalchemy import text
    result = {}
    # Primary: PostGIS geometry
    try:
        rows = db.execute(text("""
            SELECT id, ST_Y(location_geom) as lat, ST_X(location_geom) as lng
            FROM projects
            WHERE id = ANY(:ids) AND location_geom IS NOT NULL
        """), {"ids": project_ids}).fetchall()
        result = {r.id: {"latitude": r.lat, "longitude": r.lng} for r in rows}
    except Exception:
        pass
    # Fallback: locations table
    missing = [pid for pid in project_ids if pid not in result]
    if missing:
        try:
            rows2 = db.execute(text("""
                SELECT p.id, l.latitude, l.longitude, l.polygon, l.geojson, l.center_lat, l.center_lng
                FROM projects p JOIN locations l ON p.location_id = l.id
                WHERE p.id = ANY(:ids) AND l.latitude IS NOT NULL
            """), {"ids": missing}).fetchall()
            for r in rows2:
                result[r.id] = {
                    "latitude": float(r.latitude) if r.latitude else None,
                    "longitude": float(r.longitude) if r.longitude else None,
                    "polygon": r.polygon,
                    "geojson": r.geojson,
                }
        except Exception:
            pass
    return result


@router.get("/{item_id}/geo")
def get_project_geo(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get project with geographic coordinates for map."""
    require_permission(current_user, "projects.read")
    project = service.get_by_id_or_404(db, item_id)
    coords = _get_project_coordinates(db, [item_id])
    geo = coords.get(item_id, {})
    return {
        "id": project.id,
        "name": project.name,
        "code": project.code,
        "latitude": geo.get("latitude"),
        "longitude": geo.get("longitude"),
        "polygon": geo.get("polygon"),
        "geojson": geo.get("geojson"),
        "region_id": project.region_id,
        "area_id": project.area_id,
    }
