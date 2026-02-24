"""Admin endpoints for project management"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.project import Project
from app.models.area import Area
from app.models.region import Region
from app.schemas.project import ProjectUpdate

router = APIRouter(prefix="/admin/projects", tags=["Admin - Projects"])


@router.get("/unassigned")
def get_unassigned_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all projects without area assignment (area_id is NULL)"""
    
    # Only admins can access this
    if current_user.role.code != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
    
    projects = db.query(Project).filter(
        Project.area_id.is_(None)
    ).all()
    
    result = []
    for project in projects:
        result.append({
            "id": project.id,
            "name": project.name,
            "code": project.code,
            "status": project.status,
            "region_id": project.region_id,
            "area_id": project.area_id,
            "manager_id": project.manager_id,
        })
    
    return {
        "total": len(result),
        "projects": result
    }


@router.put("/assign-area/{project_id}")
def assign_project_to_area(
    project_id: int,
    area_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Assign a project to an area"""
    
    # Only admins can access this
    if current_user.role.code != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
    
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get area
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    
    # Update project
    project.area_id = area_id
    project.region_id = area.region_id  # Also update region from area
    
    db.commit()
    db.refresh(project)
    
    return {
        "message": "Project assigned successfully",
        "project": {
            "id": project.id,
            "name": project.name,
            "area_id": project.area_id,
            "region_id": project.region_id,
            "area_name": area.name,
            "region_name": area.region.name if area.region else None
        }
    }


@router.put("/batch-assign")
def batch_assign_projects(
    assignments: List[dict],  # [{"project_id": 1, "area_id": 12}, ...]
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Batch assign multiple projects to areas"""
    
    # Only admins can access this
    if current_user.role.code != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
    
    results = []
    errors = []
    
    for assignment in assignments:
        try:
            project_id = assignment.get("project_id")
            area_id = assignment.get("area_id")
            
            if not project_id or not area_id:
                errors.append({"error": "Missing project_id or area_id", "data": assignment})
                continue
            
            # Get project
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                errors.append({"project_id": project_id, "error": "Project not found"})
                continue
            
            # Get area
            area = db.query(Area).filter(Area.id == area_id).first()
            if not area:
                errors.append({"project_id": project_id, "error": f"Area {area_id} not found"})
                continue
            
            # Update project
            project.area_id = area_id
            project.region_id = area.region_id
            
            results.append({
                "project_id": project.id,
                "project_name": project.name,
                "area_id": area.id,
                "area_name": area.name
            })
            
        except Exception as e:
            errors.append({"project_id": project_id, "error": str(e)})
    
    db.commit()
    
    return {
        "success_count": len(results),
        "error_count": len(errors),
        "results": results,
        "errors": errors
    }


@router.get("/by-area/{area_id}")
def get_projects_by_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all projects in a specific area"""
    
    # Check if area exists
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    
    projects = db.query(Project).filter(Project.area_id == area_id).all()
    
    result = []
    for project in projects:
        result.append({
            "id": project.id,
            "name": project.name,
            "code": project.code,
            "status": project.status,
            "manager_id": project.manager_id,
            "area_name": area.name,
            "region_name": area.region.name if area.region else None
        })
    
    return {
        "area": {
            "id": area.id,
            "name": area.name,
            "region_name": area.region.name if area.region else None
        },
        "total": len(result),
        "projects": result
    }
