# app/services/calendar_service.py
"""Calendar and scheduling service."""
from datetime import date
from typing import Any, Dict, List

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.equipment_assignment import EquipmentAssignment
from app.models.equipment_maintenance import EquipmentMaintenance
from app.models.milestone import Milestone
from app.models.project import Project
from app.models.work_order import WorkOrder


class CalendarService:
    """Service for calendar and scheduling operations."""

    def get_user_calendar(
        self, db: Session, user_id: int, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Get user's calendar events."""
        events = []

        # Get user's project assignments
        from app.models.project_assignment import ProjectAssignment

        assignments = (
            db.query(ProjectAssignment, Project)
            .join(Project)
            .filter(
                and_(
                    ProjectAssignment.user_id == user_id,
                    ProjectAssignment.status == "active",
                    or_(
                        and_(
                            Project.start_date <= end_date,
                            or_(
                                Project.end_date >= start_date, Project.end_date == None
                            ),
                        )
                    ),
                )
            )
            .all()
        )

        for assignment, project in assignments:
            # Project duration events
            project_start = max(project.start_date, start_date)
            project_end = min(project.end_date or end_date, end_date)

            if project_end >= project_start:
                events.append(
                    {
                        "type": "project",
                        "id": f"project_{project.id}",
                        "title": f"פרויקט: {project.name}",
                        "start": project_start.isoformat(),
                        "end": project_end.isoformat(),
                        "all_day": True,
                        "color": "#4CAF50",
                        "details": {
                            "project_id": project.id,
                            "role": assignment.role,
                            "status": project.status,
                        },
                    }
                )

        # Get work orders
        work_orders = (
            db.query(WorkOrder)
            .filter(
                and_(
                    WorkOrder.created_by_id == user_id,
                    WorkOrder.work_start_date <= end_date,
                    WorkOrder.work_end_date >= start_date,
                )
            )
            .all()
        )

        for order in work_orders:
            events.append(
                {
                    "type": "work_order",
                    "id": f"work_order_{order.id}",
                    "title": f"הזמנת עבודה: {order.order_number}",
                    "start": order.work_start_date.isoformat(),
                    "end": order.work_end_date.isoformat(),
                    "all_day": True,
                    "color": "#FF9800",
                    "details": {"order_id": order.id, "status": order.status},
                }
            )

        # Get milestones
        milestones = (
            db.query(Milestone)
            .join(Project)
            .join(ProjectAssignment)
            .filter(
                and_(
                    ProjectAssignment.user_id == user_id,
                    Milestone.due_date >= start_date,
                    Milestone.due_date <= end_date,
                    Milestone.status != "completed",
                )
            )
            .all()
        )

        for milestone in milestones:
            events.append(
                {
                    "type": "milestone",
                    "id": f"milestone_{milestone.id}",
                    "title": f"אבן דרך: {milestone.name}",
                    "start": milestone.due_date.isoformat(),
                    "end": milestone.due_date.isoformat(),
                    "all_day": True,
                    "color": "#9C27B0",
                    "details": {
                        "milestone_id": milestone.id,
                        "project_id": milestone.project_id,
                        "status": milestone.status,
                    },
                }
            )

        return events

    def get_equipment_calendar(
        self, db: Session, equipment_id: int, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Get equipment calendar events."""
        events = []

        # Equipment assignments
        assignments = (
            db.query(EquipmentAssignment)
            .filter(
                and_(
                    EquipmentAssignment.equipment_id == equipment_id,
                    EquipmentAssignment.status != "cancelled",
                    or_(
                        and_(
                            EquipmentAssignment.start_date <= end_date,
                            EquipmentAssignment.end_date >= start_date,
                        )
                    ),
                )
            )
            .all()
        )

        for assignment in assignments:
            events.append(
                {
                    "type": "assignment",
                    "id": f"assignment_{assignment.id}",
                    "title": f"הקצאה לפרויקט {assignment.project_id}",
                    "start": assignment.start_date.isoformat(),
                    "end": assignment.end_date.isoformat(),
                    "all_day": True,
                    "color": "#2196F3",
                    "details": {
                        "assignment_id": assignment.id,
                        "project_id": assignment.project_id,
                        "status": assignment.status,
                    },
                }
            )

        # Maintenance
        maintenance = (
            db.query(EquipmentMaintenance)
            .filter(
                and_(
                    EquipmentMaintenance.equipment_id == equipment_id,
                    EquipmentMaintenance.scheduled_date >= start_date,
                    EquipmentMaintenance.scheduled_date <= end_date,
                    EquipmentMaintenance.status != "cancelled",
                )
            )
            .all()
        )

        for maint in maintenance:
            events.append(
                {
                    "type": "maintenance",
                    "id": f"maintenance_{maint.id}",
                    "title": f"תחזוקה: {maint.maintenance_type}",
                    "start": maint.scheduled_date.isoformat(),
                    "end": maint.scheduled_date.isoformat(),
                    "all_day": True,
                    "color": "#F44336",
                    "details": {
                        "maintenance_id": maint.id,
                        "type": maint.maintenance_type,
                        "status": maint.status,
                    },
                }
            )

        return events

    def get_project_calendar(
        self, db: Session, project_id: int, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Get project calendar events."""
        events = []

        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            return events

        # Project timeline
        if project.start_date <= end_date and (
            not project.end_date or project.end_date >= start_date
        ):
            events.append(
                {
                    "type": "project_timeline",
                    "id": f"project_timeline_{project.id}",
                    "title": project.name,
                    "start": max(project.start_date, start_date).isoformat(),
                    "end": min(project.end_date or end_date, end_date).isoformat(),
                    "all_day": True,
                    "color": "#4CAF50",
                    "details": {"project_id": project.id, "status": project.status},
                }
            )

        # Milestones
        milestones = (
            db.query(Milestone)
            .filter(
                and_(
                    Milestone.project_id == project_id,
                    Milestone.due_date >= start_date,
                    Milestone.due_date <= end_date,
                )
            )
            .all()
        )

        for milestone in milestones:
            events.append(
                {
                    "type": "milestone",
                    "id": f"milestone_{milestone.id}",
                    "title": f"אבן דרך: {milestone.name}",
                    "start": milestone.due_date.isoformat(),
                    "end": milestone.due_date.isoformat(),
                    "all_day": False,
                    "color": "#9C27B0"
                    if milestone.status != "completed"
                    else "#4CAF50",
                    "details": {
                        "milestone_id": milestone.id,
                        "status": milestone.status,
                    },
                }
            )

        # Work orders
        work_orders = (
            db.query(WorkOrder)
            .filter(
                and_(
                    WorkOrder.project_id == project_id,
                    WorkOrder.work_start_date <= end_date,
                    WorkOrder.work_end_date >= start_date,
                )
            )
            .all()
        )

        for order in work_orders:
            events.append(
                {
                    "type": "work_order",
                    "id": f"work_order_{order.id}",
                    "title": f"הזמנה: {order.order_number}",
                    "start": order.work_start_date.isoformat(),
                    "end": order.work_end_date.isoformat(),
                    "all_day": True,
                    "color": "#FF9800",
                    "details": {
                        "order_id": order.id,
                        "supplier_id": order.supplier_id,
                        "status": order.status,
                    },
                }
            )

        # Equipment assignments
        equipment = (
            db.query(EquipmentAssignment)
            .filter(
                and_(
                    EquipmentAssignment.project_id == project_id,
                    EquipmentAssignment.status != "cancelled",
                    EquipmentAssignment.start_date <= end_date,
                    EquipmentAssignment.end_date >= start_date,
                )
            )
            .all()
        )

        for eq in equipment:
            events.append(
                {
                    "type": "equipment",
                    "id": f"equipment_{eq.id}",
                    "title": f"ציוד: {eq.equipment_id}",
                    "start": eq.start_date.isoformat(),
                    "end": eq.end_date.isoformat(),
                    "all_day": True,
                    "color": "#00BCD4",
                    "details": {
                        "assignment_id": eq.id,
                        "equipment_id": eq.equipment_id,
                        "status": eq.status,
                    },
                }
            )

        return events

    def get_holidays(self, db: Session, year: int) -> List[Dict[str, Any]]:
        """Get holidays for a year."""
        # In production, this would come from a holiday table
        # Here are Israeli holidays for example
        holidays = [
            {"date": f"{year}-01-01", "name": "ראש השנה האזרחי"},
            {"date": f"{year}-04-15", "name": "פסח"},
            {"date": f"{year}-04-21", "name": "שביעי של פסח"},
            {"date": f"{year}-05-01", "name": "יום העצמאות"},
            {"date": f"{year}-06-04", "name": "שבועות"},
            {"date": f"{year}-09-15", "name": "ראש השנה"},
            {"date": f"{year}-09-24", "name": "יום כיפור"},
            {"date": f"{year}-09-29", "name": "סוכות"},
            {"date": f"{year}-10-06", "name": "שמיני עצרת"},
        ]

        return holidays

    def check_availability(
        self,
        db: Session,
        resource_type: str,  # "user", "equipment", "location"
        resource_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Check resource availability."""
        conflicts = []
        available = True

        if resource_type == "equipment":
            # Check equipment assignments
            assignments = (
                db.query(EquipmentAssignment)
                .filter(
                    and_(
                        EquipmentAssignment.equipment_id == resource_id,
                        EquipmentAssignment.status != "cancelled",
                        or_(
                            and_(
                                EquipmentAssignment.start_date <= start_date,
                                EquipmentAssignment.end_date >= start_date,
                            ),
                            and_(
                                EquipmentAssignment.start_date <= end_date,
                                EquipmentAssignment.end_date >= end_date,
                            ),
                            and_(
                                EquipmentAssignment.start_date >= start_date,
                                EquipmentAssignment.end_date <= end_date,
                            ),
                        ),
                    )
                )
                .all()
            )

            if assignments:
                available = False
                for assignment in assignments:
                    conflicts.append(
                        {
                            "type": "assignment",
                            "start": assignment.start_date.isoformat(),
                            "end": assignment.end_date.isoformat(),
                            "project_id": assignment.project_id,
                        }
                    )

            # Check maintenance
            maintenance = (
                db.query(EquipmentMaintenance)
                .filter(
                    and_(
                        EquipmentMaintenance.equipment_id == resource_id,
                        EquipmentMaintenance.scheduled_date >= start_date,
                        EquipmentMaintenance.scheduled_date <= end_date,
                        EquipmentMaintenance.status != "cancelled",
                    )
                )
                .all()
            )

            if maintenance:
                available = False
                for maint in maintenance:
                    conflicts.append(
                        {
                            "type": "maintenance",
                            "date": maint.scheduled_date.isoformat(),
                        }
                    )

        elif resource_type == "user":
            # Check user assignments
            from app.models.project_assignment import ProjectAssignment

            assignments = (
                db.query(ProjectAssignment)
                .filter(
                    and_(
                        ProjectAssignment.user_id == resource_id,
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
                                ProjectAssignment.start_date <= end_date,
                                or_(
                                    ProjectAssignment.end_date >= end_date,
                                    ProjectAssignment.end_date == None,
                                ),
                            ),
                        ),
                    )
                )
                .all()
            )

            # Check if user is overallocated
            total_hours = sum(
                a.hours_allocated for a in assignments if a.hours_allocated
            )

            if total_hours >= 40:  # Weekly hours threshold
                available = False
                conflicts.append(
                    {"type": "overallocation", "allocated_hours": total_hours}
                )

        return {"available": available, "conflicts": conflicts}
