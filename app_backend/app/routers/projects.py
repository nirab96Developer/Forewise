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
    """List projects. Pass my_projects=true to filter by user assignments."""
    require_permission(current_user, "projects.read")
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
    
    # Add relationships
    if item.region:
        result["region"] = {"id": item.region.id, "name": item.region.name}
    if item.area:
        result["area"] = {"id": item.area.id, "name": item.area.name}
    
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
    """Get lat/lng for projects from location_geom (PostGIS)."""
    if not project_ids:
        return {}
    from sqlalchemy import text
    try:
        rows = db.execute(text("""
            SELECT id, ST_Y(location_geom) as lat, ST_X(location_geom) as lng
            FROM projects 
            WHERE id = ANY(:ids) AND location_geom IS NOT NULL
        """), {"ids": project_ids}).fetchall()
        return {r.id: {"latitude": r.lat, "longitude": r.lng} for r in rows}
    except Exception as e:
        print(f"Warning: Could not get coordinates: {e}")
        return {}


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
        "region_id": project.region_id,
        "area_id": project.area_id,
    }
