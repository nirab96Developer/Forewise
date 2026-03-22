"""Project milestone service."""
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import (BusinessLogicException, NotFoundException,
                                 ValidationException)
from app.models.milestone import Milestone
from app.models.project import Project
from app.schemas.milestone import (MilestoneCreate, MilestoneResponse,
                                   MilestoneStatus, MilestoneType,
                                   MilestoneUpdate)


class MilestoneService:
    """Project milestone management."""

    def __init__(self):
        pass

    async def create(
        self, db: Session, *, obj_in: MilestoneCreate, created_by_id: int
    ) -> MilestoneResponse:
        """Create project milestone."""
        # Validate project
        project = (
            db.query(Project)
            .filter(Project.id == obj_in.project_id, Project.is_active == True)
            .first()
        )

        if not project:
            raise NotFoundException(f"Project {obj_in.project_id} not found")

        # Create milestone
        data = obj_in.dict(exclude_unset=True)
        data.pop('created_by_id', None)
        data.pop('planned_date', None)
        data.pop('actual_date', None)
        data.pop('completion_notes', None)
        milestone = Milestone(**data)
        db.add(milestone)
        db.commit()
        db.refresh(milestone)

        return MilestoneResponse.from_orm(milestone)

    async def update_status(
        self,
        db: Session,
        milestone_id: int,
        status: MilestoneStatus,
        completion_percentage: int = None,
        notes: str = None,
        updated_by_id: int = None,
    ) -> MilestoneResponse:
        """Update milestone status."""
        milestone = (
            db.query(Milestone)
            .filter(Milestone.id == milestone_id, Milestone.is_active == True)
            .first()
        )

        if not milestone:
            raise NotFoundException(f"Milestone {milestone_id} not found")

        milestone.status = status
        milestone.progress_percentage = completion_percentage or 0
        milestone.notes = notes

        if status == MilestoneStatus.COMPLETED:
            milestone.completed_date = date.today()

        db.commit()
        db.refresh(milestone)

        return MilestoneResponse.from_orm(milestone)

    async def get_project_milestones(
        self, db: Session, project_id: int, include_completed: bool = True
    ) -> List[MilestoneResponse]:
        """Get all milestones for a project."""
        query = db.query(Milestone).filter(
            Milestone.project_id == project_id, Milestone.is_active == True
        )

        if not include_completed:
            query = query.filter(Milestone.status != MilestoneStatus.COMPLETED)

        milestones = query.order_by(Milestone.due_date).all()

        return [MilestoneResponse.from_orm(m) for m in milestones]

    async def get_milestone_timeline(
        self, db: Session, project_id: int
    ) -> Dict[str, Any]:
        """Get milestone timeline with dependencies."""
        milestones = (
            db.query(Milestone)
            .filter(Milestone.project_id == project_id, Milestone.is_active == True)
            .order_by(Milestone.due_date)
            .all()
        )

        timeline = []

        for milestone in milestones:
            # Calculate days until due
            days_until = (milestone.due_date - date.today()).days

            timeline_item = {
                "id": milestone.id,
                "name": milestone.name,
                "due_date": milestone.due_date.isoformat(),
                "status": milestone.status,
                "completion_percentage": milestone.progress_percentage,
                "days_until_due": days_until,
                "is_overdue": days_until < 0
                and milestone.status != MilestoneStatus.COMPLETED,
                "depends_on": milestone.depends_on_milestone_id,
                "deliverables": milestone.deliverables,
            }

            # Add completion info
            if milestone.status == MilestoneStatus.COMPLETED:
                timeline_item["completed_date"] = milestone.completed_date.isoformat()
                timeline_item["days_early_late"] = (
                    milestone.due_date - milestone.completed_date
                ).days

            timeline.append(timeline_item)

        return {
            "project_id": project_id,
            "milestones": timeline,
            "total_milestones": len(milestones),
            "completed": sum(
                1 for m in milestones if m.status == MilestoneStatus.COMPLETED
            ),
            "overdue": sum(
                1
                for m in milestones
                if m.due_date < date.today() and m.status != MilestoneStatus.COMPLETED
            ),
        }

    async def get_upcoming_milestones(
        self, db: Session, days_ahead: int = 30, user_id: int = None
    ) -> List[Dict[str, Any]]:
        """Get upcoming milestones."""
        end_date = date.today() + timedelta(days=days_ahead)

        query = (
            db.query(Milestone, Project.name)
            .join(Project, Project.id == Milestone.project_id)
            .filter(
                Milestone.due_date <= end_date,
                Milestone.due_date >= date.today(),
                Milestone.status != MilestoneStatus.COMPLETED,
                Milestone.is_active == True,
                Project.is_active == True,
            )
        )

        rows = query.order_by(Milestone.due_date).all()

        results = []
        for milestone, project_name in rows:
            days_until = (milestone.due_date - date.today()).days

            results.append(
                {
                    "id": milestone.id,
                    "project_id": milestone.project_id,
                    "project_name": project_name,
                    "milestone_name": milestone.name,
                    "due_date": milestone.due_date.isoformat(),
                    "days_until": days_until,
                    "status": milestone.status,
                    "completion_percentage": milestone.progress_percentage,
                    "is_critical": days_until <= 7,
                }
            )

        return results



