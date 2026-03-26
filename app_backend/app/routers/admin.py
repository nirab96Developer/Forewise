"""Admin management endpoints - ניהול מלא למנהל המערכת"""
import secrets
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.models.role import Role
from app.models.project import Project
from app.models.area import Area
from app.models.region import Region
from app.models.department import Department
from app.models.location import Location
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.project import ProjectUpdate
from app.core.security import get_password_hash

router = APIRouter(prefix="/admin", tags=["Admin Management"])


def verify_admin(current_user: User) -> None:
    """Verify that current user is admin"""
    if not current_user.role or current_user.role.code != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access this endpoint"
        )


# ============================================================================
# DASHBOARD & STATISTICS
# ============================================================================

@router.get("/dashboard")
async def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive admin dashboard data"""
    verify_admin(current_user)
    
    # Get counts
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_projects = db.query(Project).count()
    unassigned_projects = db.query(Project).filter(Project.area_id.is_(None)).count()
    total_areas = db.query(Area).count()
    total_regions = db.query(Region).count()
    
    # Get users by role
    users_by_role = db.query(
        Role.name,
        func.count(User.id).label('count')
    ).join(User).group_by(Role.name).all()
    
    # Get projects by status
    projects_by_status = db.query(
        Project.status,
        func.count(Project.id).label('count')
    ).group_by(Project.status).all()
    
    return {
        "statistics": {
            "users": {
                "total": total_users,
                "active": active_users,
                "inactive": total_users - active_users
            },
            "projects": {
                "total": total_projects,
                "unassigned": unassigned_projects,
                "assigned": total_projects - unassigned_projects
            },
            "geography": {
                "regions": total_regions,
                "areas": total_areas
            }
        },
        "users_by_role": [{"role": r.name, "count": r.count} for r in users_by_role],
        "projects_by_status": [{"status": p.status, "count": p.count} for p in projects_by_status]
    }


# ============================================================================
# USER MANAGEMENT
# ============================================================================

@router.get("/users")
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    role_id: Optional[int] = None,
    region_id: Optional[int] = None,
    area_id: Optional[int] = None,
    is_active: Optional[bool] = None
):
    """Get all users with filters"""
    verify_admin(current_user)
    
    query = db.query(User).options(
        joinedload(User.role),
        joinedload(User.region),
        joinedload(User.area),
        joinedload(User.department)
    )
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(
            User.username.ilike(search_term),
            User.email.ilike(search_term),
            User.full_name.ilike(search_term)
        ))
    
    if role_id:
        query = query.filter(User.role_id == role_id)
    if region_id:
        query = query.filter(User.region_id == region_id)
    if area_id:
        query = query.filter(User.area_id == area_id)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [{
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "phone": u.phone,
            "is_active": u.is_active,
            "role": {
                "id": u.role.id,
                "code": u.role.code,
                "name": u.role.name
            } if u.role else None,
            "region": {
                "id": u.region.id,
                "name": u.region.name
            } if u.region else None,
            "area": {
                "id": u.area.id,
                "name": u.area.name
            } if u.area else None,
            "department": {
                "id": u.department.id,
                "name": u.department.name
            } if u.department else None,
            "created_at": u.created_at,
            "last_login": u.last_login
        } for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/users")
async def create_user(
    user_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new user"""
    verify_admin(current_user)
    
    # Check if username/email already exists
    existing = db.query(User).filter(
        or_(
            User.username == user_data.get("username"),
            User.email == user_data.get("email")
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # Create new user
    new_user = User(
        username=user_data["username"],
        email=user_data["email"],
        full_name=user_data["full_name"],
        password_hash=get_password_hash(user_data.get("password", secrets.token_urlsafe(16))),
        phone=user_data.get("phone"),
        role_id=user_data.get("role_id"),
        region_id=user_data.get("region_id"),
        area_id=user_data.get("area_id"),
        department_id=user_data.get("department_id"),
        is_active=user_data.get("is_active", True)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "User created successfully",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name
        }
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user details"""
    verify_admin(current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    for field, value in user_data.items():
        if field == "password":
            user.password_hash = get_password_hash(value)
        elif hasattr(user, field):
            setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return {
        "message": "User updated successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete (deactivate) a user"""
    verify_admin(current_user)
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "User deactivated successfully"}


# ============================================================================
# PROJECT ASSIGNMENT
# ============================================================================

@router.get("/projects/unassigned")
async def get_unassigned_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all projects without area assignment"""
    verify_admin(current_user)
    
    projects = db.query(Project).filter(
        or_(
            Project.area_id.is_(None),
            Project.region_id.is_(None)
        )
    ).all()
    
    return {
        "total": len(projects),
        "projects": [{
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "status": p.status,
            "region_id": p.region_id,
            "area_id": p.area_id,
            "manager_id": p.manager_id
        } for p in projects]
    }


@router.put("/projects/{project_id}/assign")
async def assign_project(
    project_id: int,
    assignment: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Assign project to area/region/manager"""
    verify_admin(current_user)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update assignment
    if "area_id" in assignment:
        area = db.query(Area).filter(Area.id == assignment["area_id"]).first()
        if not area:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Area not found"
            )
        project.area_id = area.id
        project.region_id = area.region_id
    
    if "manager_id" in assignment:
        manager = db.query(User).filter(User.id == assignment["manager_id"]).first()
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Manager not found"
            )
        project.manager_id = manager.id
    
    if "location_id" in assignment:
        project.location_id = assignment["location_id"]
    
    db.commit()
    db.refresh(project)
    
    return {
        "message": "Project assigned successfully",
        "project": {
            "id": project.id,
            "name": project.name,
            "area_id": project.area_id,
            "region_id": project.region_id,
            "manager_id": project.manager_id
        }
    }


@router.put("/projects/batch-assign")
async def batch_assign_projects(
    assignments: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Batch assign multiple projects"""
    verify_admin(current_user)
    
    results = []
    errors = []
    
    for assignment in assignments:
        try:
            project_id = assignment.get("project_id")
            area_id = assignment.get("area_id")
            
            if not project_id:
                errors.append({"error": "Missing project_id", "data": assignment})
                continue
            
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                errors.append({"project_id": project_id, "error": "Project not found"})
                continue
            
            if area_id:
                area = db.query(Area).filter(Area.id == area_id).first()
                if not area:
                    errors.append({"project_id": project_id, "error": f"Area {area_id} not found"})
                    continue
                
                project.area_id = area_id
                project.region_id = area.region_id
            
            if "manager_id" in assignment:
                project.manager_id = assignment["manager_id"]
            
            results.append({
                "project_id": project.id,
                "project_name": project.name,
                "area_id": project.area_id,
                "region_id": project.region_id
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


# ============================================================================
# ROLE & PERMISSION MANAGEMENT
# ============================================================================

@router.get("/roles")
async def get_all_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all roles with permissions - optimized with single query for user counts"""
    verify_admin(current_user)
    
    # Get user counts per role in a single query (fixes N+1)
    from sqlalchemy import func as sql_func
    user_counts = dict(
        db.query(User.role_id, sql_func.count(User.id))
        .group_by(User.role_id)
        .all()
    )
    
    roles = db.query(Role).filter(Role.is_active == True).all()
    
    return [{
        "id": r.id,
        "code": r.code,
        "name": r.name,
        "description": r.description,
        "user_count": user_counts.get(r.id, 0)
    } for r in roles]


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user's role"""
    verify_admin(current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    role = db.query(Role).filter(Role.id == role_data["role_id"]).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role not found"
        )
    
    user.role_id = role.id
    
    # Update region/area based on role
    if role.code == "REGION_MANAGER":
        if "region_id" not in role_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Region ID required for REGION_MANAGER role"
            )
        user.region_id = role_data["region_id"]
        user.area_id = None
    
    elif role.code == "AREA_MANAGER":
        if "area_id" not in role_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Area ID required for AREA_MANAGER role"
            )
        area = db.query(Area).filter(Area.id == role_data["area_id"]).first()
        if area:
            user.area_id = area.id
            user.region_id = area.region_id
    
    elif role.code == "ACCOUNTANT":
        # Accountant can be at region or area level
        if "area_id" in role_data:
            area = db.query(Area).filter(Area.id == role_data["area_id"]).first()
            if area:
                user.area_id = area.id
                user.region_id = area.region_id
        elif "region_id" in role_data:
            user.region_id = role_data["region_id"]
            user.area_id = None
    
    db.commit()
    
    return {
        "message": "User role updated successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": role.name,
            "region_id": user.region_id,
            "area_id": user.area_id
        }
    }


# ============================================================================
# GEOGRAPHIC MANAGEMENT
# ============================================================================

@router.get("/regions")
async def get_all_regions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all regions with their areas"""
    verify_admin(current_user)
    
    regions = db.query(Region).options(joinedload(Region.areas)).all()
    
    return [{
        "id": r.id,
        "name": r.name,
        "code": r.code,
        "manager_id": r.manager_id,
        "area_count": len(r.areas),
        "areas": [{
            "id": a.id,
            "name": a.name,
            "code": a.code,
            "manager_id": a.manager_id
        } for a in r.areas]
    } for r in regions]


@router.put("/regions/{region_id}/manager")
async def update_region_manager(
    region_id: int,
    manager_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update region manager"""
    verify_admin(current_user)
    
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    
    manager = db.query(User).filter(User.id == manager_data["manager_id"]).first()
    if not manager:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manager not found"
        )
    
    # Update region manager
    region.manager_id = manager.id
    
    # Update manager's role and region
    region_mgr_role = db.query(Role).filter(Role.code == "REGION_MANAGER").first()
    if not region_mgr_role:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Role REGION_MANAGER not found")
    manager.role_id = region_mgr_role.id
    manager.region_id = region.id
    manager.area_id = None
    
    db.commit()
    
    return {
        "message": "Region manager updated successfully",
        "region": {
            "id": region.id,
            "name": region.name,
            "manager": manager.full_name
        }
    }


@router.put("/areas/{area_id}/manager")
async def update_area_manager(
    area_id: int,
    manager_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update area manager"""
    verify_admin(current_user)
    
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found"
        )
    
    manager = db.query(User).filter(User.id == manager_data["manager_id"]).first()
    if not manager:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manager not found"
        )
    
    # Update area manager
    area.manager_id = manager.id
    
    # Update manager's role and area
    area_mgr_role = db.query(Role).filter(Role.code == "AREA_MANAGER").first()
    if not area_mgr_role:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Role AREA_MANAGER not found")
    manager.role_id = area_mgr_role.id
    manager.area_id = area.id
    manager.region_id = area.region_id
    
    db.commit()
    
    return {
        "message": "Area manager updated successfully",
        "area": {
            "id": area.id,
            "name": area.name,
            "manager": manager.full_name
        }
    }


# ============================================================================
# SYSTEM HEALTH & MAINTENANCE
# ============================================================================

@router.get("/system/health")
async def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get system health status"""
    verify_admin(current_user)
    
    try:
        # Test database connection
        from sqlalchemy import text as sa_text
        db.execute(sa_text("SELECT 1"))
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    # Get system statistics
    active_sessions = db.query(User).filter(
        User.last_login > datetime.utcnow() - timedelta(minutes=30)
    ).count()
    
    return {
        "status": "operational",
        "database": db_status,
        "active_sessions": active_sessions,
        "timestamp": datetime.utcnow()
    }


@router.post("/system/sync-database")
async def sync_database(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sync database relationships and fix inconsistencies"""
    verify_admin(current_user)
    
    fixed = {
        "projects_without_region": 0,
        "users_without_role": 0,
        "areas_without_region": 0
    }
    
    # Fix projects without region but with area
    projects = db.query(Project).filter(
        and_(
            Project.area_id.isnot(None),
            Project.region_id.is_(None)
        )
    ).all()
    
    for project in projects:
        area = db.query(Area).filter(Area.id == project.area_id).first()
        if area and area.region_id:
            project.region_id = area.region_id
            fixed["projects_without_region"] += 1
    
    # Fix users without role
    users = db.query(User).filter(User.role_id.is_(None)).all()
    viewer_role = db.query(Role).filter(Role.code == "VIEWER").first()
    
    for user in users:
        if viewer_role:
            user.role_id = viewer_role.id
            fixed["users_without_role"] += 1
    
    db.commit()
    
    return {
        "message": "Database sync completed",
        "fixed": fixed
    }