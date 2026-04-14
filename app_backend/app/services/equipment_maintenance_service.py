# app/services/equipment_maintenance_service.py
"""Equipment maintenance management service."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.equipment import Equipment
from app.models.equipment_maintenance import EquipmentMaintenance
from app.schemas.equipment_maintenance import (MaintenanceCreate,
                                               MaintenanceUpdate)


class EquipmentMaintenanceService:
    """Service for equipment maintenance operations."""

    def get_maintenance(
        self, db: Session, maintenance_id: int
    ) -> Optional[EquipmentMaintenance]:
        """Get maintenance record by ID."""
        return (
            db.query(EquipmentMaintenance)
            .filter(
                and_(
                    EquipmentMaintenance.id == maintenance_id,
                    EquipmentMaintenance.is_active == True,
                )
            )
            .first()
        )

    def get_maintenance_records(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        equipment_id: Optional[int] = None,
        status: Optional[str] = None,
        maintenance_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[EquipmentMaintenance]:
        """Get list of maintenance records with filters."""
        query = db.query(EquipmentMaintenance).filter(
            EquipmentMaintenance.is_active == True
        )

        if equipment_id:
            query = query.filter(EquipmentMaintenance.equipment_id == equipment_id)
        if status:
            query = query.filter(EquipmentMaintenance.status == status)
        if maintenance_type:
            query = query.filter(
                EquipmentMaintenance.maintenance_type == maintenance_type
            )
        if start_date:
            query = query.filter(EquipmentMaintenance.scheduled_date >= start_date)
        if end_date:
            query = query.filter(EquipmentMaintenance.scheduled_date <= end_date)

        return (
            query.order_by(EquipmentMaintenance.scheduled_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def schedule_maintenance(
        self, db: Session, maintenance: MaintenanceCreate, created_by_id: int
    ) -> EquipmentMaintenance:
        """Schedule new equipment maintenance."""
        # Check equipment exists
        equipment = (
            db.query(Equipment).filter(Equipment.id == maintenance.equipment_id).first()
        )

        if not equipment:
            raise ValueError("Equipment not found")

        # Check for conflicts
        conflicts = self._check_maintenance_conflicts(
            db,
            equipment_id=maintenance.equipment_id,
            scheduled_date=maintenance.scheduled_date,
        )

        if conflicts:
            raise ValueError("Maintenance already scheduled for this date")

        # Create maintenance record
        description_text = maintenance.description or maintenance.title
        maintenance_type_val = (
            maintenance.maintenance_type.value
            if hasattr(maintenance.maintenance_type, "value")
            else str(maintenance.maintenance_type)
        )
        db_maintenance = EquipmentMaintenance(
            equipment_id=maintenance.equipment_id,
            maintenance_type=maintenance_type_val,
            scheduled_date=maintenance.scheduled_date,
            description=description_text,
            scheduled_by=created_by_id,
            status="scheduled",
            is_active=True,
        )

        db.add(db_maintenance)
        db.commit()
        db.refresh(db_maintenance)

        # Send notification
        self._send_maintenance_notification(db, db_maintenance, "scheduled")

        return db_maintenance

    def update_maintenance(
        self, db: Session, maintenance_id: int, maintenance: MaintenanceUpdate
    ) -> Optional[EquipmentMaintenance]:
        """Update maintenance record."""
        db_maintenance = self.get_maintenance(db, maintenance_id)
        if not db_maintenance:
            return None

        # Don't allow updating completed maintenance
        if db_maintenance.status == "completed":
            raise ValueError("Cannot update completed maintenance")

        update_data = maintenance.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_maintenance, field, value)

        db_maintenance.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_maintenance)
        return db_maintenance

    def start_maintenance(
        self,
        db: Session,
        maintenance_id: int,
        performed_by_id: int,
        actual_start: Optional[datetime] = None,
    ) -> Optional[EquipmentMaintenance]:
        """Start maintenance work."""
        db_maintenance = self.get_maintenance(db, maintenance_id)
        if not db_maintenance:
            return None

        if db_maintenance.status != "scheduled":
            raise ValueError("Maintenance not in scheduled status")

        db_maintenance.status = "in_progress"
        start = actual_start or datetime.utcnow()
        db_maintenance.performed_date = (
            start.date() if isinstance(start, datetime) else date.today()
        )
        db_maintenance.performed_by = performed_by_id
        db_maintenance.updated_at = datetime.utcnow()

        # Update equipment status
        equipment = (
            db.query(Equipment)
            .filter(Equipment.id == db_maintenance.equipment_id)
            .first()
        )
        if equipment:
            equipment.status = "maintenance"

        db.commit()
        db.refresh(db_maintenance)
        return db_maintenance

    def complete_maintenance(
        self,
        db: Session,
        maintenance_id: int,
        actual_cost: Decimal,
        parts_used: Optional[Dict[str, Any]] = None,
        completion_notes: Optional[str] = None,
        next_maintenance_date: Optional[date] = None,
    ) -> Optional[EquipmentMaintenance]:
        """Complete maintenance work."""
        db_maintenance = self.get_maintenance(db, maintenance_id)
        if not db_maintenance:
            return None

        if db_maintenance.status != "in_progress":
            raise ValueError("Maintenance not in progress")

        db_maintenance.status = "completed"
        db_maintenance.completed_at = datetime.utcnow()
        if actual_cost is not None:
            db_maintenance.total_cost = actual_cost
        if parts_used:
            db_maintenance.parts_replaced = str(parts_used)
        if completion_notes:
            db_maintenance.notes = completion_notes
        db_maintenance.performed_date = date.today()
        db_maintenance.updated_at = datetime.utcnow()

        # Update equipment
        equipment = (
            db.query(Equipment)
            .filter(Equipment.id == db_maintenance.equipment_id)
            .first()
        )
        if equipment:
            equipment.status = "available"
            equipment.last_maintenance = date.today()
            equipment.next_maintenance = next_maintenance_date

        db.commit()
        db.refresh(db_maintenance)

        # Schedule next maintenance if provided
        if next_maintenance_date:
            self._schedule_next_maintenance(
                db,
                equipment_id=db_maintenance.equipment_id,
                next_date=next_maintenance_date,
                maintenance_type=db_maintenance.maintenance_type,
            )

        return db_maintenance

    def cancel_maintenance(self, db: Session, maintenance_id: int, reason: str) -> bool:
        """Cancel scheduled maintenance."""
        db_maintenance = self.get_maintenance(db, maintenance_id)
        if not db_maintenance:
            return False

        if db_maintenance.status not in ["scheduled", "in_progress"]:
            raise ValueError("Cannot cancel maintenance in current status")

        previous_status = db_maintenance.status
        db_maintenance.status = "cancelled"
        db_maintenance.updated_at = datetime.utcnow()
        if reason:
            note = f"Cancelled: {reason}"
            db_maintenance.notes = (
                f"{db_maintenance.notes}\n{note}"
                if db_maintenance.notes
                else note
            )

        # Update equipment status if was in maintenance
        if previous_status == "in_progress":
            equipment = (
                db.query(Equipment)
                .filter(Equipment.id == db_maintenance.equipment_id)
                .first()
            )
            if equipment and equipment.status == "maintenance":
                equipment.status = "available"

        db.commit()
        return True

    def get_maintenance_schedule(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        equipment_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Get maintenance schedule."""
        query = db.query(EquipmentMaintenance).filter(
            and_(
                EquipmentMaintenance.scheduled_date >= start_date,
                EquipmentMaintenance.scheduled_date <= end_date,
                EquipmentMaintenance.status.in_(["scheduled", "in_progress"]),
                EquipmentMaintenance.is_active == True,
            )
        )

        if equipment_ids:
            query = query.filter(EquipmentMaintenance.equipment_id.in_(equipment_ids))

        maintenances = query.all()

        eq_ids = {m.equipment_id for m in maintenances}
        code_by_id: Dict[int, Optional[str]] = {}
        if eq_ids:
            rows = (
                db.query(Equipment.id, Equipment.code)
                .filter(Equipment.id.in_(eq_ids))
                .all()
            )
            code_by_id = {r.id: r.code for r in rows}

        schedule = []
        for maintenance in maintenances:
            schedule.append(
                {
                    "maintenance_id": maintenance.id,
                    "equipment_id": maintenance.equipment_id,
                    "equipment_code": code_by_id.get(maintenance.equipment_id),
                    "maintenance_type": maintenance.maintenance_type,
                    "scheduled_date": maintenance.scheduled_date.isoformat(),
                    "status": maintenance.status,
                }
            )

        schedule.sort(key=lambda x: x["scheduled_date"])

        return schedule

    def get_overdue_maintenance(self, db: Session) -> List[Dict[str, Any]]:
        """Get overdue maintenance tasks."""
        today = date.today()

        # Scheduled but past due date
        overdue = (
            db.query(EquipmentMaintenance)
            .filter(
                and_(
                    EquipmentMaintenance.scheduled_date < today,
                    EquipmentMaintenance.status == "scheduled",
                    EquipmentMaintenance.is_active == True,
                )
            )
            .all()
        )

        # Equipment past next maintenance date
        equipment_overdue = (
            db.query(Equipment)
            .filter(
                and_(
                    Equipment.next_maintenance != None,
                    Equipment.next_maintenance < today,
                    Equipment.is_active == True,
                )
            )
            .all()
        )

        results = []

        overdue_eq_ids = {m.equipment_id for m in overdue}
        overdue_codes: Dict[int, Optional[str]] = {}
        if overdue_eq_ids:
            rows = (
                db.query(Equipment.id, Equipment.code)
                .filter(Equipment.id.in_(overdue_eq_ids))
                .all()
            )
            overdue_codes = {r.id: r.code for r in rows}

        # Add scheduled overdue
        for maintenance in overdue:
            days_overdue = (today - maintenance.scheduled_date).days
            results.append(
                {
                    "type": "scheduled",
                    "maintenance_id": maintenance.id,
                    "equipment_id": maintenance.equipment_id,
                    "equipment_code": overdue_codes.get(maintenance.equipment_id),
                    "maintenance_type": maintenance.maintenance_type,
                    "scheduled_date": maintenance.scheduled_date.isoformat(),
                    "days_overdue": days_overdue,
                }
            )

        # Add equipment overdue
        for equipment in equipment_overdue:
            days_overdue = (today - equipment.next_maintenance).days
            nm = equipment.next_maintenance
            results.append(
                {
                    "type": "routine",
                    "equipment_id": equipment.id,
                    "equipment_code": equipment.code,
                    "next_maintenance_date": nm.isoformat() if nm else None,
                    "days_overdue": days_overdue,
                    "priority": "high" if days_overdue > 30 else "medium",
                }
            )

        return results

    def get_maintenance_costs(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        equipment_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get maintenance cost analysis."""
        query = db.query(EquipmentMaintenance).filter(
            and_(
                EquipmentMaintenance.status == "completed",
                EquipmentMaintenance.completed_at >= start_date,
                EquipmentMaintenance.completed_at <= end_date,
                EquipmentMaintenance.is_active == True,
            )
        )

        if equipment_id:
            query = query.filter(EquipmentMaintenance.equipment_id == equipment_id)

        maintenances = query.all()

        # Calculate totals (model stores actual spend as total_cost)
        total_cost = sum(
            (m.total_cost or Decimal("0")) for m in maintenances
        )
        total_estimated = Decimal("0")

        # Group by type
        by_type = {}
        for maintenance in maintenances:
            mtype = maintenance.maintenance_type
            if mtype not in by_type:
                by_type[mtype] = {
                    "count": 0,
                    "actual_cost": Decimal("0"),
                    "estimated_cost": Decimal("0"),
                }

            by_type[mtype]["count"] += 1
            by_type[mtype]["actual_cost"] += maintenance.total_cost or 0

        # Calculate variance (no estimated columns on model)
        cost_variance = total_cost - total_estimated
        variance_percent = (
            (cost_variance / total_estimated * 100) if total_estimated else 0
        )

        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_maintenances": len(maintenances),
            "total_cost": float(total_cost),
            "total_estimated": float(total_estimated),
            "cost_variance": float(cost_variance),
            "variance_percent": float(variance_percent),
            "by_type": {
                k: {
                    "count": v["count"],
                    "actual_cost": float(v["actual_cost"]),
                    "estimated_cost": float(v["estimated_cost"]),
                }
                for k, v in by_type.items()
            },
        }

    def _check_maintenance_conflicts(
        self,
        db: Session,
        equipment_id: int,
        scheduled_date: date,
        exclude_id: Optional[int] = None,
    ) -> List[EquipmentMaintenance]:
        """Check for maintenance conflicts."""
        query = db.query(EquipmentMaintenance).filter(
            and_(
                EquipmentMaintenance.equipment_id == equipment_id,
                EquipmentMaintenance.scheduled_date == scheduled_date,
                EquipmentMaintenance.status != "cancelled",
                EquipmentMaintenance.is_active == True,
            )
        )

        if exclude_id:
            query = query.filter(EquipmentMaintenance.id != exclude_id)

        return query.all()

    def _schedule_next_maintenance(
        self, db: Session, equipment_id: int, next_date: date, maintenance_type: str
    ):
        """Schedule next routine maintenance."""
        # Create new maintenance record
        next_maintenance = EquipmentMaintenance(
            equipment_id=equipment_id,
            maintenance_type=maintenance_type,
            scheduled_date=next_date,
            description=f"Routine {maintenance_type} maintenance",
            status="scheduled",
            is_active=True,
        )
        db.add(next_maintenance)
        db.commit()

    def _send_maintenance_notification(
        self, db: Session, maintenance: EquipmentMaintenance, event_type: str
    ):
        """Send maintenance notification."""
        # Import here to avoid circular dependency
        from app.services.notification_service import NotificationService

        NotificationService()

        # Implement notification logic based on event type
        pass
