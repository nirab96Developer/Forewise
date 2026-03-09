# app/services/project_assignment_service.py
"""Project assignment management service."""
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.project import Project
from app.models.project_assignment import ProjectAssignment
from app.models.user import User
from app.schemas.project_assignment import AssignmentCreate, AssignmentUpdate


class ProjectAssignmentService:
    """Service for project assignment operations."""

    def get_assignment(
        self, db: Session, assignment_id: int
    ) -> Optional[ProjectAssignment]:
        """Get project assignment by ID."""
        return (
            db.query(ProjectAssignment)
            .options(
                joinedload(ProjectAssignment.project),
                joinedload(ProjectAssignment.user),
                joinedload(ProjectAssignment.assigned_by),
            )
            .filter(
                and_(
                    ProjectAssignment.id == assignment_id,
                    ProjectAssignment.is_active == True,
                )
            )
            .first()
        )

    def get_assignments(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        include_past: bool = False,
    ) -> List[ProjectAssignment]:
        """Get list of project assignments with filters."""
        query = db.query(ProjectAssignment).filter(ProjectAssignment.is_active == True)

        if not include_past:
            query = query.filter(ProjectAssignment.status == "active")

        if project_id:
            query = query.filter(ProjectAssignment.project_id == project_id)
        if user_id:
            query = query.filter(ProjectAssignment.user_id == user_id)
        if role:
            query = query.filter(ProjectAssignment.role == role)
        if status:
            query = query.filter(ProjectAssignment.status == status)

        return (
            query.order_by(ProjectAssignment.start_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_assignments(
        self,
        db: Session,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        include_past: bool = False,
    ) -> int:
        """Count project assignments matching filters."""
        query = db.query(ProjectAssignment).filter(ProjectAssignment.is_active == True)

        if not include_past:
            query = query.filter(ProjectAssignment.status == "active")

        if project_id:
            query = query.filter(ProjectAssignment.project_id == project_id)
        if user_id:
            query = query.filter(ProjectAssignment.user_id == user_id)
        if role:
            query = query.filter(ProjectAssignment.role == role)
        if status:
            query = query.filter(ProjectAssignment.status == status)

        return query.count()

    def assign_user_to_project(
        self, db: Session, assignment: AssignmentCreate, assigned_by_id: int
    ) -> ProjectAssignment:
        """Assign user to project."""
        # Check if project exists
        project = db.query(Project).filter(Project.id == assignment.project_id).first()

        if not project:
            raise ValueError("Project not found")

        # Check if user exists
        user = db.query(User).filter(User.id == assignment.user_id).first()

        if not user:
            raise ValueError("User not found")

        # Check for existing assignment
        existing = (
            db.query(ProjectAssignment)
            .filter(
                and_(
                    ProjectAssignment.project_id == assignment.project_id,
                    ProjectAssignment.user_id == assignment.user_id,
                    ProjectAssignment.status == "active",
                    ProjectAssignment.is_active == True,
                )
            )
            .first()
        )

        if existing:
            raise ValueError("User already assigned to this project")

        # Create assignment
        db_assignment = ProjectAssignment(
            project_id=assignment.project_id,
            user_id=assignment.user_id,
            role=assignment.role,
            responsibilities=getattr(assignment, 'responsibilities', None) or getattr(assignment, 'responsibility', None),
            start_date=assignment.start_date or date.today(),
            end_date=assignment.end_date,
            estimated_hours=assignment.estimated_hours,
            can_approve_reports=getattr(assignment, 'can_approve_worklogs', False) or getattr(assignment, 'can_approve_reports', False),
            can_manage_team=assignment.can_manage_team or False,
            assigned_by_id=assigned_by_id,
            status="active",
            created_at=datetime.utcnow(),
        )

        db.add(db_assignment)
        db.commit()
        db.refresh(db_assignment)

        # Send notification
        self._send_assignment_notification(db, db_assignment, "assigned")

        return db_assignment

    def update_assignment(
        self, db: Session, assignment_id: int, assignment: AssignmentUpdate
    ) -> Optional[ProjectAssignment]:
        """Update project assignment."""
        db_assignment = self.get_assignment(db, assignment_id)
        if not db_assignment:
            return None

        update_data = assignment.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_assignment, field, value)

        db_assignment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_assignment)
        return db_assignment

    def remove_user_from_project(
        self, db: Session, assignment_id: int, reason: Optional[str] = None
    ) -> bool:
        """Remove user from project."""
        db_assignment = self.get_assignment(db, assignment_id)
        if not db_assignment:
            return False

        db_assignment.status = "inactive"
        db_assignment.end_date = date.today()
        db_assignment.removal_reason = reason
        db_assignment.updated_at = datetime.utcnow()

        db.commit()

        # Send notification
        self._send_assignment_notification(db, db_assignment, "removed")

        return True

    def get_project_team(
        self,
        db: Session,
        project_id: int,
        active_only: bool = True,
        include_inactive: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get project team members."""
        query = (
            db.query(ProjectAssignment, User)
            .join(User, ProjectAssignment.user_id == User.id)
            .filter(
                and_(
                    ProjectAssignment.project_id == project_id,
                    ProjectAssignment.is_active == True,
                )
            )
        )

        if active_only and not include_inactive:
            query = query.filter(ProjectAssignment.status == "active")

        results = query.all()

        team = []
        for assignment, user in results:
            team.append(
                {
                    "assignment_id": assignment.id,
                    "user_id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": assignment.role,
                    "responsibility": assignment.responsibilities,
                    "start_date": assignment.start_date.isoformat(),
                    "end_date": assignment.end_date.isoformat()
                    if assignment.end_date
                    else None,
                    "estimated_hours": float(assignment.estimated_hours)
                    if assignment.estimated_hours
                    else None,
                    "can_approve_worklogs": getattr(assignment, 'can_approve_reports', False),
                    "can_manage_team": assignment.can_manage_team,
                }
            )

        return team

    def get_user_projects(
        self, db: Session, user_id: int, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get user's project assignments."""
        query = (
            db.query(ProjectAssignment, Project)
            .join(Project)
            .filter(
                and_(
                    ProjectAssignment.user_id == user_id,
                    ProjectAssignment.is_active == True,
                )
            )
        )

        if active_only:
            query = query.filter(
                and_(ProjectAssignment.status == "active", Project.status == "active")
            )

        results = query.all()

        projects = []
        for assignment, project in results:
            projects.append(
                {
                    "assignment_id": assignment.id,
                    "project_id": project.id,
                    "project_name": project.name,
                    "project_status": project.status,
                    "role": assignment.role,
                    "start_date": assignment.start_date.isoformat(),
                    "end_date": assignment.end_date.isoformat()
                    if assignment.end_date
                    else None,
                    "estimated_hours": float(assignment.estimated_hours)
                    if assignment.estimated_hours
                    else None,
                }
            )

        return projects

    def can_access_assignment(
        self, db: Session, user_id: int, assignment_id: int
    ) -> bool:
        """Check if user can access a specific assignment."""
        assignment = (
            db.query(ProjectAssignment)
            .filter(ProjectAssignment.id == assignment_id, ProjectAssignment.is_active == True)
            .first()
        )
        if not assignment:
            return False
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        if hasattr(user, 'role') and user.role and getattr(user.role, 'code', None) in ('admin', 'region_manager', 'area_manager'):
            return True
        return assignment.user_id == user_id

    def complete_assignment(
        self, db: Session, assignment_id: int, completion_notes: Optional[str] = None
    ) -> Optional[ProjectAssignment]:
        """Mark assignment as completed."""
        db_assignment = self.get_assignment(db, assignment_id)
        if not db_assignment:
            return None
        db_assignment.status = "completed"
        db_assignment.end_date = date.today()
        if completion_notes and hasattr(db_assignment, 'notes'):
            db_assignment.notes = completion_notes
        db_assignment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_assignment)
        return db_assignment

    def bulk_assign_users(
        self,
        db: Session,
        project_id: int,
        user_ids: List[int],
        role: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        assigned_by_id: int = None,
    ) -> Dict[str, Any]:
        """Bulk assign multiple users to a project."""
        results = {"assigned": [], "skipped": [], "errors": []}
        for uid in user_ids:
            try:
                from app.schemas.project_assignment import AssignmentCreate
                assignment_data = AssignmentCreate(
                    project_id=project_id,
                    user_id=uid,
                    role=role,
                    start_date=start_date or date.today(),
                    end_date=end_date,
                )
                self.assign_user_to_project(db, assignment_data, assigned_by_id or 0)
                results["assigned"].append(uid)
            except ValueError as e:
                results["skipped"].append({"user_id": uid, "reason": str(e)})
            except Exception as e:
                results["errors"].append({"user_id": uid, "error": str(e)})
        return results

    def get_workload_statistics(
        self,
        db: Session,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get workload statistics for a user."""
        _start = start_date or date.today().replace(day=1)
        _end = end_date or date.today()
        analysis = self.get_workload_analysis(db, [user_id], _start, _end)
        return analysis.get(user_id, {"total_hours": 0, "project_count": 0, "utilization_percent": 0})

    def check_user_availability(
        self,
        db: Session,
        user_id: int,
        start_date: date,
        end_date: date,
        hours_required: float,
    ) -> Dict[str, Any]:
        """Check if user has capacity for the requested hours in the period."""
        analysis = self.get_workload_analysis(db, [user_id], start_date, end_date)
        data = analysis.get(user_id, {"available_hours": 0, "total_hours": 0})
        available = data.get("available_hours", 0) - data.get("total_hours", 0)
        return {
            "user_id": user_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hours_required": hours_required,
            "hours_available": round(max(available, 0), 2),
            "is_available": available >= hours_required,
            "current_utilization_percent": data.get("utilization_percent", 0),
        }

    def check_assignment_conflicts(
        self,
        db: Session,
        user_id: int,
        project_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Check for overlapping assignments for a user in a date range."""
        conflicts = (
            db.query(ProjectAssignment)
            .filter(
                and_(
                    ProjectAssignment.user_id == user_id,
                    ProjectAssignment.status == "active",
                    ProjectAssignment.is_active == True,
                    ProjectAssignment.project_id != project_id,
                    ProjectAssignment.start_date <= end_date,
                    or_(
                        ProjectAssignment.end_date.is_(None),
                        ProjectAssignment.end_date >= start_date,
                    ),
                )
            )
            .all()
        )
        return {
            "has_conflicts": len(conflicts) > 0,
            "conflict_count": len(conflicts),
            "conflicts": [
                {"assignment_id": c.id, "project_id": c.project_id, "role": c.role}
                for c in conflicts
            ],
        }

    def transfer_assignments(
        self,
        db: Session,
        from_user_id: int,
        to_user_id: int,
        project_ids: Optional[List[int]] = None,
        transfer_reason: str = "",
        transferred_by_id: int = None,
    ) -> Dict[str, Any]:
        """Transfer all active assignments from one user to another."""
        query = db.query(ProjectAssignment).filter(
            and_(
                ProjectAssignment.user_id == from_user_id,
                ProjectAssignment.status == "active",
                ProjectAssignment.is_active == True,
            )
        )
        if project_ids:
            query = query.filter(ProjectAssignment.project_id.in_(project_ids))

        assignments = query.all()
        transferred = []
        for a in assignments:
            a.user_id = to_user_id
            a.updated_at = datetime.utcnow()
            transferred.append(a.id)

        db.commit()
        return {"transferred": transferred, "count": len(transferred), "reason": transfer_reason}

    def check_user_project_access(
        self,
        db: Session,
        user_id: int,
        project_id: int,
        permission: Optional[str] = None,
    ) -> bool:
        """Check if user has access to project."""
        assignment = (
            db.query(ProjectAssignment)
            .filter(
                and_(
                    ProjectAssignment.project_id == project_id,
                    ProjectAssignment.user_id == user_id,
                    ProjectAssignment.status == "active",
                    ProjectAssignment.is_active == True,
                )
            )
            .first()
        )

        if not assignment:
            return False

        # Check specific permission
        if permission:
            if permission == "approve_worklogs":
                return assignment.can_approve_worklogs
            elif permission == "manage_team":
                return assignment.can_manage_team

        return True

    def get_assignment_statistics(
        self,
        db: Session,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get assignment statistics."""
        query = db.query(ProjectAssignment).filter(ProjectAssignment.is_active == True)

        if user_id:
            query = query.filter(ProjectAssignment.user_id == user_id)
        if project_id:
            query = query.filter(ProjectAssignment.project_id == project_id)

        assignments = query.all()

        # Calculate statistics
        total = len(assignments)
        active = len([a for a in assignments if a.status == "active"])

        # Role distribution
        role_distribution = {}
        for assignment in assignments:
            if assignment.role not in role_distribution:
                role_distribution[assignment.role] = 0
            role_distribution[assignment.role] += 1

        # Total allocated hours
        total_hours = sum(
            a.hours_allocated
            for a in assignments
            if a.hours_allocated and a.status == "active"
        )

        # Average assignment duration
        durations = []
        for assignment in assignments:
            if assignment.end_date:
                duration = (assignment.end_date - assignment.start_date).days
            else:
                duration = (date.today() - assignment.start_date).days
            durations.append(duration)

        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_assignments": total,
            "active_assignments": active,
            "inactive_assignments": total - active,
            "role_distribution": role_distribution,
            "total_allocated_hours": float(total_hours),
            "average_duration_days": round(avg_duration, 1),
        }

    def get_workload_analysis(
        self, db: Session, user_ids: List[int], start_date: date, end_date: date
    ) -> Dict[int, Dict[str, Any]]:
        """Analyze user workload based on assignments."""
        workload = {}

        for user_id in user_ids:
            # Get active assignments in period
            assignments = (
                db.query(ProjectAssignment)
                .filter(
                    and_(
                        ProjectAssignment.user_id == user_id,
                        ProjectAssignment.status == "active",
                        or_(
                            and_(
                                ProjectAssignment.start_date <= start_date,
                                or_(
                                    ProjectAssignment.end_date >= start_date,
                                    ProjectAssignment.end_date == None,
                                ),
                            ),
                            and_(
                                ProjectAssignment.start_date >= start_date,
                                ProjectAssignment.start_date <= end_date,
                            ),
                        ),
                    )
                )
                .all()
            )

            # Calculate total allocated hours
            total_hours = 0
            project_count = 0

            for assignment in assignments:
                if assignment.estimated_hours:
                    # Calculate hours in period
                    assign_start = max(assignment.start_date, start_date)
                    assign_end = min(assignment.end_date or end_date, end_date)

                    if assign_end >= assign_start:
                        period_days = (assign_end - assign_start).days + 1
                        total_period_days = (
                            (assignment.end_date or end_date) - assignment.start_date
                        ).days + 1

                        # Prorate hours
                        period_hours = (
                            assignment.estimated_hours * period_days / total_period_days
                        )
                        total_hours += period_hours
                        project_count += 1

            # Calculate utilization (assuming 8 hours per day)
            work_days = ((end_date - start_date).days + 1) * 5 / 7  # Rough weekday calc
            available_hours = work_days * 8
            utilization = (
                (total_hours / available_hours * 100) if available_hours else 0
            )

            workload[user_id] = {
                "total_hours": round(total_hours, 2),
                "project_count": project_count,
                "available_hours": round(available_hours, 2),
                "utilization_percent": round(utilization, 2),
                "status": self._get_workload_status(utilization),
            }

        return workload

    def _get_workload_status(self, utilization: float) -> str:
        """Get workload status based on utilization."""
        if utilization < 50:
            return "underutilized"
        elif utilization <= 80:
            return "optimal"
        elif utilization <= 100:
            return "full"
        else:
            return "overloaded"

    def _send_assignment_notification(
        self, db: Session, assignment: ProjectAssignment, event_type: str
    ):
        """Send assignment notification."""
        # Import here to avoid circular dependency
        from app.services.notification_service import NotificationService

        notification_service = NotificationService()

        if event_type == "assigned":
            notification_service.create_notification(
                db=db,
                user_id=assignment.user_id,
                title="New Project Assignment",
                message=f"You have been assigned to project: {assignment.project.name if assignment.project else 'Unknown'}",
                notification_type="info",
                channels=["in_app", "email"],
                metadata={"project_id": assignment.project_id},
            )
        elif event_type == "removed":
            notification_service.create_notification(
                db=db,
                user_id=assignment.user_id,
                title="Project Assignment Removed",
                message=f"You have been removed from project: {assignment.project.name if assignment.project else 'Unknown'}",
                notification_type="warning",
                channels=["in_app"],
                metadata={"project_id": assignment.project_id},
            )
