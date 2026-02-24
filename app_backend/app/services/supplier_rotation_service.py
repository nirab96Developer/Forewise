# app/services/supplier_rotation_service.py
"""Supplier rotation (fair queue) service."""
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.supplier import Supplier
from app.models.supplier_rotation import SupplierRotation
from app.models.work_order import WorkOrder
from app.schemas.supplier_rotation import RotationCreate, RotationUpdate


class SupplierRotationService:
    """Service for supplier rotation (fair queue) operations."""

    def get_rotation(
        self, db: Session, supplier_id: int, equipment_type: Optional[str] = None
    ) -> Optional[SupplierRotation]:
        """Get supplier rotation record."""
        query = db.query(SupplierRotation).filter(
            and_(
                SupplierRotation.supplier_id == supplier_id,
                SupplierRotation.is_active == True,
            )
        )

        if equipment_type:
            query = query.filter(SupplierRotation.equipment_type == equipment_type)

        return query.first()

    def get_rotation_queue(
        self, db: Session, area_id: int, equipment_type: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get supplier rotation queue for area and equipment type."""
        # Get eligible suppliers
        suppliers = (
            db.query(Supplier, SupplierRotation)
            .join(SupplierRotation, Supplier.id == SupplierRotation.supplier_id)
            .filter(
                and_(
                    # NOTE: Supplier doesn't have area_id
                    # Supplier.area_id == area_id,
                    Supplier.status == "active",
                    Supplier.is_active == True,
                    func.jsonb_contains(
                        Supplier.equipment_types, f'["{equipment_type}"]'
                    ),
                    SupplierRotation.is_active == True,
                )
            )
            .all()
        )

        # Calculate priority scores
        queue = []
        for supplier, rotation in suppliers:
            # Calculate days since last assignment
            days_since_last = 999
            if rotation.last_assigned_at:
                days_since_last = (datetime.utcnow() - rotation.last_assigned_at).days

            # Calculate score (higher = more priority)
            # Factors: days waiting, total assignments (inverse), performance rating
            score = (
                days_since_last * 10
                + (100 / (rotation.assignment_count + 1)) * 5  # Weight: days waiting
                + (supplier.rating or 3) * 2  # Weight: fairness  # Weight: performance
            )

            queue.append(
                {
                    "supplier_id": supplier.id,
                    "supplier_name": supplier.name,
                    "equipment_type": equipment_type,
                    "last_assigned": rotation.last_assigned_at.isoformat()
                    if rotation.last_assigned_at
                    else None,
                    "days_waiting": days_since_last,
                    "assignment_count": rotation.assignment_count,
                    "total_hours": float(rotation.total_hours),
                    "rating": supplier.rating,
                    "priority_score": round(score, 2),
                }
            )

        # Sort by priority score (highest first)
        queue.sort(key=lambda x: x["priority_score"], reverse=True)

        return queue[:limit]

    def get_next_supplier(
        self,
        db: Session,
        area_id: int,
        equipment_type: str,
        exclude_ids: Optional[List[int]] = None,
    ) -> Optional[int]:
        """Get next supplier in rotation."""
        queue = self.get_rotation_queue(db, area_id, equipment_type)

        if exclude_ids:
            queue = [s for s in queue if s["supplier_id"] not in exclude_ids]

        if not queue:
            return None

        return queue[0]["supplier_id"]

    def update_rotation_after_assignment(
        self,
        db: Session,
        supplier_id: int,
        equipment_type: str,
        estimated_hours: float = 0,
    ) -> SupplierRotation:
        """Update rotation after work order assignment."""
        rotation = self.get_rotation(db, supplier_id, equipment_type)

        if not rotation:
            # Create new rotation record
            rotation = SupplierRotation(
                supplier_id=supplier_id,
                equipment_type=equipment_type,
                last_assigned_at=datetime.utcnow(),
                assignment_count=1,
                total_hours=estimated_hours,
                priority_score=100.0,
                created_at=datetime.utcnow(),
            )
            db.add(rotation)
        else:
            # Update existing
            rotation.last_assigned_at = datetime.utcnow()
            rotation.assignment_count += 1
            rotation.total_hours += estimated_hours
            rotation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(rotation)
        return rotation

    def update_rotation_after_completion(
        self,
        db: Session,
        supplier_id: int,
        equipment_type: str,
        actual_hours: float,
        performance_score: Optional[float] = None,
    ) -> SupplierRotation:
        """Update rotation after work order completion."""
        rotation = self.get_rotation(db, supplier_id, equipment_type)

        if rotation:
            rotation.total_hours = (
                rotation.total_hours - rotation.total_hours + actual_hours
            )

            if performance_score:
                # Update priority based on performance
                rotation.priority_score = (
                    rotation.priority_score * 0.8 + performance_score * 20
                )  # 80% old score, 20% new performance

            rotation.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(rotation)

        return rotation

    def reset_supplier_rotation(
        self, db: Session, supplier_id: int, equipment_type: Optional[str] = None
    ) -> int:
        """Reset supplier rotation records."""
        query = db.query(SupplierRotation).filter(
            SupplierRotation.supplier_id == supplier_id
        )

        if equipment_type:
            query = query.filter(SupplierRotation.equipment_type == equipment_type)

        count = query.update(
            {
                "assignment_count": 0,
                "total_hours": 0,
                "last_assigned_at": None,
                "priority_score": 100.0,
                "updated_at": datetime.utcnow(),
            }
        )

        db.commit()
        return count

    def get_supplier_rotation_statistics(
        self, db: Session, supplier_id: int
    ) -> Dict[str, Any]:
        """Get supplier rotation statistics."""
        rotations = (
            db.query(SupplierRotation)
            .filter(
                and_(
                    SupplierRotation.supplier_id == supplier_id,
                    SupplierRotation.is_active == True,
                )
            )
            .all()
        )

        total_assignments = sum(r.assignment_count for r in rotations)
        total_hours = sum(r.total_hours for r in rotations)

        equipment_breakdown = []
        for rotation in rotations:
            equipment_breakdown.append(
                {
                    "equipment_type": rotation.equipment_type,
                    "assignments": rotation.assignment_count,
                    "hours": float(rotation.total_hours),
                    "last_assigned": rotation.last_assigned_at.isoformat()
                    if rotation.last_assigned_at
                    else None,
                    "days_since_last": (
                        (datetime.utcnow() - rotation.last_assigned_at).days
                    )
                    if rotation.last_assigned_at
                    else None,
                }
            )

        # Get recent work orders
        recent_orders = (
            db.query(WorkOrder)
            .filter(
                and_(
                    WorkOrder.supplier_id == supplier_id,
                    WorkOrder.created_at >= datetime.utcnow() - timedelta(days=30),
                )
            )
            .all()
        )

        acceptance_rate = 0
        if recent_orders:
            accepted = len(
                [o for o in recent_orders if o.status in ["accepted", "completed"]]
            )
            acceptance_rate = (accepted / len(recent_orders)) * 100

        return {
            "supplier_id": supplier_id,
            "total_assignments": total_assignments,
            "total_hours": float(total_hours),
            "equipment_types": len(rotations),
            "acceptance_rate_30d": round(acceptance_rate, 2),
            "equipment_breakdown": equipment_breakdown,
        }

    def get_area_rotation_balance(
        self, db: Session, area_id: int, equipment_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get rotation balance analysis for area."""
        query = (
            db.query(
                Supplier.id,
                Supplier.name,
                SupplierRotation.equipment_type,
                SupplierRotation.assignment_count,
                SupplierRotation.total_hours,
                SupplierRotation.last_assigned_at,
            )
            .join(SupplierRotation, Supplier.id == SupplierRotation.supplier_id)
            .filter(
                and_(
                    # NOTE: Supplier doesn't have area_id
                    # Supplier.area_id == area_id,
                    Supplier.is_active == True,
                    SupplierRotation.is_active == True,
                )
            )
        )

        if equipment_type:
            query = query.filter(SupplierRotation.equipment_type == equipment_type)

        results = query.all()

        if not results:
            return {
                # "area_id": area_id,  # Supplier doesn't have area_id
                "equipment_type": equipment_type,
                "suppliers": [],
                "balance_score": 100,
            }

        # Calculate balance metrics
        suppliers_data = []
        assignment_counts = []

        for result in results:
            suppliers_data.append(
                {
                    "supplier_id": result.id,
                    "name": result.name,
                    "equipment_type": result.equipment_type,
                    "assignments": result.assignment_count,
                    "hours": float(result.total_hours),
                    "last_assigned": result.last_assigned_at.isoformat()
                    if result.last_assigned_at
                    else None,
                }
            )
            assignment_counts.append(result.assignment_count)

        # Calculate standard deviation for balance score
        if assignment_counts:
            avg = sum(assignment_counts) / len(assignment_counts)
            variance = sum((x - avg) ** 2 for x in assignment_counts) / len(
                assignment_counts
            )
            std_dev = variance**0.5

            # Balance score: 100 = perfect balance, 0 = very unbalanced
            balance_score = max(0, 100 - (std_dev * 10))
        else:
            balance_score = 100

        return {
            "area_id": area_id,
            "equipment_type": equipment_type,
            "suppliers": suppliers_data,
            "balance_score": round(balance_score, 2),
            "average_assignments": sum(assignment_counts) / len(assignment_counts)
            if assignment_counts
            else 0,
            "max_difference": max(assignment_counts) - min(assignment_counts)
            if assignment_counts
            else 0,
        }

    def enforce_rotation(
        self,
        db: Session,
        supplier_id: int,
        area_id: int,
        equipment_type: str,
        reason: str,
    ) -> bool:
        """Force supplier to back of queue (for constraint/direct assignment)."""
        # Update rotation as if they were just assigned
        self.update_rotation_after_assignment(
            db, supplier_id=supplier_id, equipment_type=equipment_type
        )

        # Log the constraint
        from app.models.supplier_constraint_log import SupplierConstraintLog

        log = SupplierConstraintLog(
            supplier_id=supplier_id,
            equipment_type=equipment_type,
            reason=reason,
            created_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()

        return True
