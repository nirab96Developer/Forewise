# app/routers/project_assignments.py
"""Project assignment management endpoints."""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import (check_project_access, get_current_active_user,
                              get_pagination_params, require_permission)
from app.schemas.common import PaginationParams
from app.schemas.project_assignment import (AssignmentCreate,
                                            AssignmentResponse,
                                            AssignmentStatistics,
                                            AssignmentUpdate,
                                            ProjectTeamResponse,
                                            UserProjectsResponse)
from app.services.activity_log_service import ActivityLogService
from app.services.project_assignment_service import ProjectAssignmentService

router = APIRouter(prefix="/project-assignments", tags=["Project Assignments"])

# Service instances
assignment_service = ProjectAssignmentService()
activity_log_service = ActivityLogService()


@router.get("")
def get_assignments(
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination_params),
    project_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    include_past: bool = Query(False),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(require_permission("project_assignments.read")),
):
    """Get list of project assignments."""
    # Apply scope filtering
    if current_user.role.code == "work_manager" and not user_id:
        user_id = current_user.id

    assignments = assignment_service.get_assignments(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
        project_id=project_id,
        user_id=user_id,
        role=role,
        status=status,
        include_past=include_past,
    )

    total = assignment_service.count_assignments(
        db=db,
        project_id=project_id,
        user_id=user_id,
        role=role,
        status=status,
        include_past=include_past,
    )

    return {
        "items": [AssignmentResponse.from_orm(a) for a in assignments],
        "total": total,
        "page": pagination.page,
        "pages": (total + pagination.limit - 1) // pagination.limit,
    }


@router.get("/my-assignments", response_model=UserProjectsResponse)
def get_my_assignments(
    db: Session = Depends(get_db),
    active_only: bool = Query(True),
    current_user=Depends(get_current_active_user),
):
    """Get current user's project assignments."""
    projects = assignment_service.get_user_projects(
        db=db, user_id=current_user.id, active_only=active_only
    )

    return UserProjectsResponse(
        user_id=current_user.id, projects=projects, total=len(projects)
    )


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(require_permission("project_assignments.read")),
):
    """Get assignment by ID."""
    assignment = assignment_service.get_assignment(db, assignment_id)

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )

    # Check access
    if not assignment_service.can_access_assignment(db, current_user.id, assignment_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this assignment",
        )

    return AssignmentResponse.from_orm(assignment)


@router.post("/", response_model=AssignmentResponse)
def create_assignment(
    assignment: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(require_permission("project_assignments.create")),
):
    """Create project assignment."""
    try:
        # Check project access
        from app.services.project_service import ProjectService

        project_service = ProjectService()

        if not project_service.can_manage_project(
            db, current_user.id, assignment.project_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot manage this project",
            )

        new_assignment = assignment_service.assign_user_to_project(
            db=db, assignment=assignment, assigned_by_id=current_user.id
        )

        # Log activity
        activity_log_service.log_activity(
            db=db,
            user_id=current_user.id,
            action="project_assignment_created",
            entity_type="project_assignment",
            entity_id=new_assignment.id,
            details={
                "project_id": assignment.project_id,
                "user_id": assignment.user_id,
                "role": assignment.role,
            },
        )

        return AssignmentResponse.from_orm(new_assignment)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: int,
    assignment: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(require_permission("project_assignments.update")),
):
    """Update project assignment."""
    try:
        # Check access
        existing = assignment_service.get_assignment(db, assignment_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
            )

        from app.services.project_service import ProjectService

        project_service = ProjectService()

        if not project_service.can_manage_project(
            db, current_user.id, existing.project_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot manage this project",
            )

        updated_assignment = assignment_service.update_assignment(
            db, assignment_id, assignment
        )

        if not updated_assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
            )

        # Log activity
        activity_log_service.log_activity(
            db=db,
            user_id=current_user.id,
            action="project_assignment_updated",
            entity_type="project_assignment",
            entity_id=assignment_id,
            details={"changes": assignment.dict(exclude_unset=True)},
        )

        return AssignmentResponse.from_orm(updated_assignment)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{assignment_id}")
def delete_assignment(
    assignment_id: int,
    reason: str = Query(..., description="Removal reason"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(require_permission("project_assignments.delete")),
):
    """Remove user from project."""
    try:
        # Check access
        existing = assignment_service.get_assignment(db, assignment_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
            )

        from app.services.project_service import ProjectService

        project_service = ProjectService()

        if not project_service.can_manage_project(
            db, current_user.id, existing.project_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot manage this project",
            )

        success = assignment_service.remove_user_from_project(db, assignment_id, reason)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to remove assignment",
            )

        # Log activity
        activity_log_service.log_activity(
            db=db,
            user_id=current_user.id,
            action="project_assignment_removed",
            entity_type="project_assignment",
            entity_id=assignment_id,
            details={"reason": reason},
        )

        return {"message": "Assignment removed successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{assignment_id}/complete")
def complete_assignment(
    assignment_id: int,
    completion_notes: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(require_permission("project_assignments.complete")),
):
    """Mark assignment as completed."""
    try:
        completed_assignment = assignment_service.complete_assignment(
            db=db, assignment_id=assignment_id, completion_notes=completion_notes
        )

        if not completed_assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
            )

        # Log activity
        activity_log_service.log_activity(
            db=db,
            user_id=current_user.id,
            action="project_assignment_completed",
            entity_type="project_assignment",
            entity_id=assignment_id,
        )

        return {"message": "Assignment completed successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Team Management Endpoints


@router.get("/project/{project_id}/team", response_model=ProjectTeamResponse)
def get_project_team(
    project_id: int,
    db: Session = Depends(get_db),
    include_inactive: bool = Query(False),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(check_project_access),
):
    """Get project team members."""
    team = assignment_service.get_project_team(
        db=db, project_id=project_id, include_inactive=include_inactive
    )

    return ProjectTeamResponse(
        project_id=project_id, team_members=team, total=len(team)
    )


@router.post("/project/{project_id}/bulk-assign")
def bulk_assign_users(
    project_id: int,
    user_ids: List[int] = Body(..., embed=True),
    role: str = Body(..., embed=True),
    start_date: Optional[date] = Body(None, embed=True),
    end_date: Optional[date] = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(check_project_access),
    __: bool = Depends(require_permission("project_assignments.bulk_assign")),
):
    """Bulk assign users to project."""
    try:
        results = assignment_service.bulk_assign_users(
            db=db,
            project_id=project_id,
            user_ids=user_ids,
            role=role,
            start_date=start_date,
            end_date=end_date,
            assigned_by_id=current_user.id,
        )

        # Log activity
        activity_log_service.log_activity(
            db=db,
            user_id=current_user.id,
            action="project_bulk_assignment",
            entity_type="project",
            entity_id=project_id,
            details=results,
        )

        return results

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/user/{user_id}/projects", response_model=UserProjectsResponse)
def get_user_projects(
    user_id: int,
    db: Session = Depends(get_db),
    active_only: bool = Query(True),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(require_permission("project_assignments.read")),
):
    """Get user's project assignments."""
    # Check if can view user's projects
    if current_user.id != user_id and current_user.role.code not in [
        "admin",
        "region_manager",
        "area_manager",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view other user's projects",
        )

    projects = assignment_service.get_user_projects(
        db=db, user_id=user_id, active_only=active_only
    )

    return UserProjectsResponse(user_id=user_id, projects=projects, total=len(projects))


@router.get("/statistics/workload")
def get_workload_statistics(
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(require_permission("project_assignments.read")),
):
    """Get workload statistics."""
    # Default to current user if not specified
    if not user_id:
        user_id = current_user.id

    statistics = assignment_service.get_workload_statistics(
        db=db, user_id=user_id, start_date=start_date, end_date=end_date
    )

    return statistics


@router.get("/availability/check")
def check_user_availability(
    user_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    hours_required: float = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(require_permission("project_assignments.check_availability")),
):
    """Check user availability for assignment."""
    availability = assignment_service.check_user_availability(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        hours_required=hours_required,
    )

    return availability


@router.get("/conflicts/check")
def check_assignment_conflicts(
    user_id: int = Query(...),
    project_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(require_permission("project_assignments.check_conflicts")),
):
    """Check for assignment conflicts."""
    conflicts = assignment_service.check_assignment_conflicts(
        db=db,
        user_id=user_id,
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
    )

    return conflicts


@router.post("/transfer")
def transfer_assignments(
    from_user_id: int = Body(..., embed=True),
    to_user_id: int = Body(..., embed=True),
    project_ids: Optional[List[int]] = Body(None, embed=True),
    transfer_reason: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
    _: bool = Depends(require_permission("project_assignments.transfer")),
):
    """Transfer assignments from one user to another."""
    try:
        results = assignment_service.transfer_assignments(
            db=db,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            project_ids=project_ids,
            transfer_reason=transfer_reason,
            transferred_by_id=current_user.id,
        )

        # Log activity
        activity_log_service.log_activity(
            db=db,
            user_id=current_user.id,
            action="assignments_transferred",
            details={
                "from_user": from_user_id,
                "to_user": to_user_id,
                "results": results,
            },
        )

        return results

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/roles/list")
def get_assignment_roles(current_user=Depends(get_current_active_user)):
    """Get available assignment roles."""
    return [
        {"value": "manager", "label": "מנהל פרויקט"},
        {"value": "supervisor", "label": "מפקח"},
        {"value": "worker", "label": "עובד"},
        {"value": "specialist", "label": "מומחה"},
        {"value": "consultant", "label": "יועץ"},
        {"value": "observer", "label": "משקיף"},
    ]
