# app/services/equipment_assignment_service.py
"""Equipment assignment management service."""
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.equipment import Equipment
from app.models.equipment_assignment import EquipmentAssignment
from app.models.project import Project
from app.schemas.equipment_assignment import AssignmentCreate, AssignmentUpdate


class EquipmentAssignmentService:
    """Service for equipment assignment operations."""

    def get_assignment(
        self, db: Session, assignment_id: int
    ) -> Optional[EquipmentAssignment]:
        """Get equipment assignment by ID."""
        return (
            db.query(EquipmentAssignment)
            .options(
                joinedload(EquipmentAssignment.equipment),
                joinedload(EquipmentAssignment.project),
                joinedload(EquipmentAssignment.assigned_by),
            )
            .filter(
                and_(
                    EquipmentAssignment.id == assignment_id,
                    EquipmentAssignment.is_active == True,
                )
            )
            .first()
        )

    def get_assignments(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        equipment_id: Optional[int] = None,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        include_past: bool = False,
    ) -> List[EquipmentAssignment]:
        """Get list of equipment assignments with filters."""
        query = db.query(EquipmentAssignment).filter(
            EquipmentAssignment.is_active == True
        )

        if equipment_id:
            query = query.filter(EquipmentAssignment.equipment_id == equipment_id)
        if project_id:
            query = query.filter(EquipmentAssignment.project_id == project_id)
        if status:
            query = query.filter(EquipmentAssignment.status == status)

        if not include_past:
            # Only active/future assignments
            query = query.filter(
                or_(
                    EquipmentAssignment.actual_end_date == None,
                    EquipmentAssignment.actual_end_date >= date.today(),
                )
            )

        return (
            query.order_by(EquipmentAssignment.start_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_assignment(
        self, db: Session, assignment: AssignmentCreate, assigned_by_id: int
    ) -> EquipmentAssignment:
        """Create new equipment assignment."""
        # Check equipment availability
        equipment = (
            db.query(Equipment).filter(Equipment.id == assignment.equipment_id).first()
        )

        if not equipment:
            raise ValueError("Equipment not found")

        if equipment.status != "available":
            raise ValueError(f"Equipment is not available (status: {equipment.status})")

        # Check for conflicts
        conflicts = self._check_assignment_conflicts(
            db,
            equipment_id=assignment.equipment_id,
            start_date=assignment.start_date,
            end_date=assignment.end_date,
        )

        if conflicts:
            raise ValueError("Equipment has conflicting assignments for this period")

        # Create assignment
        db_assignment = EquipmentAssignment(
            equipment_id=assignment.equipment_id,
            project_id=assignment.project_id,
            work_order_id=assignment.work_order_id,
            assigned_by_id=assigned_by_id,
            start_date=assignment.start_date,
            end_date=assignment.end_date,
            notes=assignment.notes,
            hourly_rate=assignment.hourly_rate or equipment.hourly_rate,
            status="scheduled",
            created_at=datetime.utcnow(),
        )

        db.add(db_assignment)

        # Update equipment status
        equipment.status = "assigned"
        equipment.current_project_id = assignment.project_id

        db.commit()
        db.refresh(db_assignment)
        return db_assignment

    def update_assignment(
        self, db: Session, assignment_id: int, assignment: AssignmentUpdate
    ) -> Optional[EquipmentAssignment]:
        """Update equipment assignment."""
        db_assignment = self.get_assignment(db, assignment_id)
        if not db_assignment:
            return None

        # Don't allow updating completed assignments
        if db_assignment.status == "completed":
            raise ValueError("Cannot update completed assignment")

        # Check for conflicts if dates changed
        if assignment.start_date or assignment.end_date:
            conflicts = self._check_assignment_conflicts(
                db,
                equipment_id=db_assignment.equipment_id,
                start_date=assignment.start_date or db_assignment.start_date,
                end_date=assignment.end_date or db_assignment.end_date,
                exclude_id=assignment_id,
            )

            if conflicts:
                raise ValueError("New dates conflict with other assignments")

        update_data = assignment.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_assignment, field, value)

        db_assignment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_assignment)
        return db_assignment

    def start_assignment(
        self, db: Session, assignment_id: int, actual_start: Optional[date] = None
    ) -> Optional[EquipmentAssignment]:
        """Start equipment assignment."""
        db_assignment = self.get_assignment(db, assignment_id)
        if not db_assignment:
            return None

        if db_assignment.status != "scheduled":
            raise ValueError("Assignment already started or completed")

        db_assignment.status = "active"
        db_assignment.actual_start_date = actual_start or date.today()
        db_assignment.updated_at = datetime.utcnow()

        # Update equipment status
        equipment = (
            db.query(Equipment)
            .filter(Equipment.id == db_assignment.equipment_id)
            .first()
        )
        if equipment:
            equipment.status = "in_use"

        db.commit()
        db.refresh(db_assignment)
        return db_assignment

    def complete_assignment(
        self,
        db: Session,
        assignment_id: int,
        actual_end: Optional[date] = None,
        actual_hours: Optional[float] = None,
        completion_notes: Optional[str] = None,
    ) -> Optional[EquipmentAssignment]:
        """Complete equipment assignment."""
        db_assignment = self.get_assignment(db, assignment_id)
        if not db_assignment:
            return None

        if db_assignment.status == "completed":
            raise ValueError("Assignment already completed")

        db_assignment.status = "completed"
        db_assignment.actual_end_date = actual_end or date.today()
        db_assignment.actual_hours = actual_hours
        db_assignment.completion_notes = completion_notes
        db_assignment.updated_at = datetime.utcnow()

        # Calculate actual cost if hours provided
        if actual_hours and db_assignment.hourly_rate:
            db_assignment.actual_cost = actual_hours * db_assignment.hourly_rate

        # Update equipment status
        equipment = (
            db.query(Equipment)
            .filter(Equipment.id == db_assignment.equipment_id)
            .first()
        )
        if equipment:
            # Check if there are other active assignments
            other_active = (
                db.query(EquipmentAssignment)
                .filter(
                    and_(
                        EquipmentAssignment.equipment_id == equipment.id,
                        EquipmentAssignment.id != assignment_id,
                        EquipmentAssignment.status == "active",
                    )
                )
                .first()
            )

            if not other_active:
                equipment.status = "available"
                equipment.current_project_id = None

        db.commit()
        db.refresh(db_assignment)
        return db_assignment

    def cancel_assignment(self, db: Session, assignment_id: int, reason: str) -> bool:
        """Cancel equipment assignment."""
        db_assignment = self.get_assignment(db, assignment_id)
        if not db_assignment:
            return False

        if db_assignment.status == "completed":
            raise ValueError("Cannot cancel completed assignment")

        db_assignment.status = "cancelled"
        db_assignment.cancellation_reason = reason
        db_assignment.cancelled_at = datetime.utcnow()
        db_assignment.updated_at = datetime.utcnow()

        # Update equipment status if it was the active assignment
        equipment = (
            db.query(Equipment)
            .filter(Equipment.id == db_assignment.equipment_id)
            .first()
        )
        if equipment and equipment.current_project_id == db_assignment.project_id:
            equipment.status = "available"
            equipment.current_project_id = None

        db.commit()
        return True

    def get_equipment_schedule(
        self, db: Session, equipment_id: int, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Get equipment schedule for date range."""
        assignments = (
            db.query(EquipmentAssignment)
            .filter(
                and_(
                    EquipmentAssignment.equipment_id == equipment_id,
                    EquipmentAssignment.is_active == True,
                    or_(
                        and_(
                            EquipmentAssignment.start_date >= start_date,
                            EquipmentAssignment.start_date <= end_date,
                        ),
                        and_(
                            EquipmentAssignment.end_date >= start_date,
                            EquipmentAssignment.end_date <= end_date,
                        ),
                        and_(
                            EquipmentAssignment.start_date <= start_date,
                            EquipmentAssignment.end_date >= end_date,
                        ),
                    ),
                )
            )
            .all()
        )

        schedule = []
        for assignment in assignments:
            schedule.append(
                {
                    "assignment_id": assignment.id,
                    "project_id": assignment.project_id,
                    "start_date": assignment.start_date.isoformat(),
                    "end_date": assignment.end_date.isoformat(),
                    "status": assignment.status,
                    "actual_start": assignment.actual_start_date.isoformat()
                    if assignment.actual_start_date
                    else None,
                    "actual_end": assignment.actual_end_date.isoformat()
                    if assignment.actual_end_date
                    else None,
                }
            )

        # Sort by start date
        schedule.sort(key=lambda x: x["start_date"])

        return schedule

    def get_project_equipment(
        self, db: Session, project_id: int, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all equipment assigned to a project."""
        query = (
            db.query(EquipmentAssignment, Equipment)
            .join(Equipment)
            .filter(
                and_(
                    EquipmentAssignment.project_id == project_id,
                    EquipmentAssignment.is_active == True,
                )
            )
        )

        if active_only:
            query = query.filter(
                EquipmentAssignment.status.in_(["scheduled", "active"])
            )

        results = query.all()

        equipment_list = []
        for assignment, equipment in results:
            equipment_list.append(
                {
                    "assignment_id": assignment.id,
                    "equipment_id": equipment.id,
                    "equipment_code": equipment.code,
                    "equipment_name": equipment.name,
                    "category": equipment.category.name if equipment.category else None,
                    "start_date": assignment.start_date.isoformat(),
                    "end_date": assignment.end_date.isoformat(),
                    "status": assignment.status,
                    "hourly_rate": float(assignment.hourly_rate)
                    if assignment.hourly_rate
                    else None,
                }
            )

        return equipment_list

    def get_availability_calendar(
        self, db: Session, equipment_ids: List[int], start_date: date, end_date: date
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get availability calendar for multiple equipment."""
        calendar = {}

        for equipment_id in equipment_ids:
            assignments = self.get_equipment_schedule(
                db, equipment_id, start_date, end_date
            )

            # Calculate available periods
            available_periods = []
            current = start_date

            for assignment in assignments:
                assign_start = date.fromisoformat(assignment["start_date"])

                # If there's a gap before this assignment
                if current < assign_start:
                    available_periods.append(
                        {
                            "start": current.isoformat(),
                            "end": (assign_start - timedelta(days=1)).isoformat(),
                        }
                    )

                # Move current to after this assignment
                assign_end = date.fromisoformat(assignment["end_date"])
                current = assign_end + timedelta(days=1)

            # If there's time after all assignments
            if current <= end_date:
                available_periods.append(
                    {"start": current.isoformat(), "end": end_date.isoformat()}
                )

            calendar[str(equipment_id)] = {
                "assignments": assignments,
                "available_periods": available_periods,
            }

        return calendar

    def _check_assignment_conflicts(
        self,
        db: Session,
        equipment_id: int,
        start_date: date,
        end_date: date,
        exclude_id: Optional[int] = None,
    ) -> List[EquipmentAssignment]:
        """Check for assignment conflicts."""
        query = db.query(EquipmentAssignment).filter(
            and_(
                EquipmentAssignment.equipment_id == equipment_id,
                EquipmentAssignment.is_active == True,
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

        if exclude_id:
            query = query.filter(EquipmentAssignment.id != exclude_id)

        return query.all()
