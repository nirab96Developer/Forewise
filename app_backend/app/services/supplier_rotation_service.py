# app/services/supplier_rotation_service.py
"""Supplier rotation (fair queue) service — aligned with SupplierRotation model."""
from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.supplier import Supplier
from app.models.supplier_rotation import SupplierRotation


class SupplierRotationService:

    def get_rotation(
        self, db: Session, supplier_id: int,
        equipment_type_id: Optional[int] = None,
    ) -> Optional[SupplierRotation]:
        # Phase 1.3: rotation now keys solely on equipment_type_id.
        # The equipment_category_id parameter that briefly existed during
        # the dual-key transition was removed.
        query = db.query(SupplierRotation).filter(
            SupplierRotation.supplier_id == supplier_id,
            SupplierRotation.is_active == True,
        )
        if equipment_type_id:
            query = query.filter(SupplierRotation.equipment_type_id == equipment_type_id)
        return query.first()

    def get_rotation_queue(
        self, db: Session, area_id: Optional[int] = None,
        equipment_type_id: Optional[int] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        query = (
            db.query(Supplier, SupplierRotation)
            .join(SupplierRotation, Supplier.id == SupplierRotation.supplier_id)
            .filter(
                Supplier.is_active == True,
                SupplierRotation.is_active == True,
                SupplierRotation.is_available != False,
            )
        )
        if area_id:
            query = query.filter(SupplierRotation.area_id == area_id)
        if equipment_type_id:
            query = query.filter(SupplierRotation.equipment_type_id == equipment_type_id)

        results = query.order_by(SupplierRotation.rotation_position.asc()).all()

        # Filter: only suppliers with equipment that has license plate
        from app.models.equipment import Equipment
        queue = []
        for supplier, rotation in results:
            eq_check = db.query(Equipment.id).filter(
                Equipment.supplier_id == supplier.id,
                Equipment.is_active == True,
                Equipment.license_plate != None,
                Equipment.license_plate != '',
            )
            if equipment_type_id:
                eq_check = eq_check.filter(Equipment.type_id == equipment_type_id)
            if not eq_check.first():
                continue  # skip suppliers without equipment/license plate
            days_since_last = 999
            if rotation.last_assignment_date:
                days_since_last = (date.today() - rotation.last_assignment_date).days

            score = (
                days_since_last * 10
                + (100 / ((rotation.total_assignments or 0) + 1)) * 5
                + (float(supplier.rating or 3)) * 2
            )

            queue.append({
                "supplier_id": supplier.id,
                "supplier_name": supplier.name,
                "equipment_type_id": rotation.equipment_type_id,
                "area_id": rotation.area_id,
                "last_assigned": rotation.last_assignment_date.isoformat() if rotation.last_assignment_date else None,
                "days_waiting": days_since_last,
                "total_assignments": rotation.total_assignments or 0,
                "rejection_count": rotation.rejection_count or 0,
                "rating": float(supplier.rating or 0),
                "priority_score": round(score, 2),
                "rotation_position": rotation.rotation_position or 0,
            })

        queue.sort(key=lambda x: x["priority_score"], reverse=True)
        return queue[:limit]

    def get_next_supplier(
        self, db: Session, area_id: Optional[int] = None,
        equipment_type_id: Optional[int] = None,
        exclude_ids: Optional[List[int]] = None,
    ) -> Optional[int]:
        queue = self.get_rotation_queue(db, area_id, equipment_type_id)
        if exclude_ids:
            queue = [s for s in queue if s["supplier_id"] not in exclude_ids]
        return queue[0]["supplier_id"] if queue else None

    def update_rotation_after_assignment(
        self, db: Session, supplier_id: int,
        equipment_type_id: Optional[int] = None,
        area_id: Optional[int] = None,
    ) -> SupplierRotation:
        # Defensive: validate FK targets BEFORE we attempt to insert. Bad data
        # used to surface as a hard 500 from PostgreSQL FK violation
        # (`supplier_rotations_equipment_type_id_fkey`) and abort the whole
        # send-to-supplier transaction. We now silently NULL-out invalid IDs
        # so rotation tracking degrades gracefully instead of breaking the
        # caller's flow.
        from sqlalchemy import text as sa_text
        if equipment_type_id is not None:
            ok = db.execute(
                sa_text("SELECT 1 FROM equipment_types WHERE id = :i"),
                {"i": equipment_type_id},
            ).fetchone()
            if not ok:
                equipment_type_id = None
        if area_id is not None:
            ok = db.execute(
                sa_text("SELECT 1 FROM areas WHERE id = :i"),
                {"i": area_id},
            ).fetchone()
            if not ok:
                area_id = None

        rotation = self.get_rotation(
            db, supplier_id, equipment_type_id=equipment_type_id,
        )

        if not rotation:
            rotation = SupplierRotation(
                supplier_id=supplier_id,
                equipment_type_id=equipment_type_id,
                area_id=area_id,
                last_assignment_date=date.today(),
                total_assignments=1,
                rejection_count=0,
                rotation_position=0,
                priority_score=100.0,
                is_active=True,
                is_available=True,
            )
            db.add(rotation)
        else:
            rotation.last_assignment_date = date.today()
            rotation.total_assignments = (rotation.total_assignments or 0) + 1
            if rotation.rotation_position is not None:
                rotation.rotation_position += 1

        db.commit()
        db.refresh(rotation)
        return rotation

    def update_rotation_after_completion(
        self, db: Session, supplier_id: int,
        equipment_type_id: Optional[int] = None,
    ) -> Optional[SupplierRotation]:
        rotation = self.get_rotation(db, supplier_id, equipment_type_id)
        if not rotation:
            return None

        rotation.successful_completions = (rotation.successful_completions or 0) + 1
        rotation.last_completion_date = date.today()

        total = rotation.total_assignments or 1
        completions = rotation.successful_completions or 0
        rotation.priority_score = round(
            (rotation.priority_score or 50) * 0.8 + (completions / total) * 100 * 0.2, 2
        )

        db.commit()
        db.refresh(rotation)
        return rotation

    def update_rotation_after_rejection(
        self, db: Session, supplier_id: int,
        equipment_type_id: Optional[int] = None,
    ) -> Optional[SupplierRotation]:
        rotation = self.get_rotation(db, supplier_id, equipment_type_id)
        if not rotation:
            return None

        rotation.rejection_count = (rotation.rejection_count or 0) + 1
        rotation.priority_score = max(0, (rotation.priority_score or 50) - 10)

        db.commit()
        db.refresh(rotation)
        return rotation

    def reset_supplier_rotation(
        self, db: Session, supplier_id: int,
        equipment_type_id: Optional[int] = None,
    ) -> Optional[SupplierRotation]:
        rotation = self.get_rotation(db, supplier_id, equipment_type_id)
        if not rotation:
            return None

        rotation.total_assignments = 0
        rotation.successful_completions = 0
        rotation.rejection_count = 0
        rotation.rotation_position = 0
        rotation.priority_score = 100.0
        rotation.last_assignment_date = None
        rotation.last_completion_date = None

        db.commit()
        db.refresh(rotation)
        return rotation

    def enforce_rotation(
        self, db: Session, supplier_id: int,
        equipment_type_id: Optional[int] = None,
    ) -> Optional[SupplierRotation]:
        """Push supplier to back of queue (after forced assignment)."""
        rotation = self.get_rotation(db, supplier_id, equipment_type_id)
        if not rotation:
            return None

        max_pos = db.query(func.max(SupplierRotation.rotation_position)).filter(
            SupplierRotation.equipment_type_id == equipment_type_id,
            SupplierRotation.is_active == True,
        ).scalar() or 0

        rotation.rotation_position = max_pos + 1
        db.commit()
        db.refresh(rotation)
        return rotation


    def select_supplier_with_checks(
        self,
        db: Session,
        area_id: Optional[int] = None,
        region_id: Optional[int] = None,
        equipment_model_id: Optional[int] = None,
        exclude_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
5-check supplier selection with area region coordinator fallback.

        Checks per supplier:
        1. Active in area/region (active_area_ids / active_region_ids contains id)
        2. Supplier is active (is_active = True)
        3. Has configured equipment of requested type (source of truth: Supplier Settings)
        4. Equipment has a license plate
        5. Equipment status = 'available'

        Selects the supplier with fewest total_assignments.
        Returns { supplier_id, fallback_level, notify_coordinator }.
        """
        from app.models.equipment import Equipment
        from app.models.equipment_model import EquipmentModel
        from app.models.equipment_category import EquipmentCategory

        def _find_in_scope(scope_filter) -> Optional[Supplier]:
            query = db.query(Supplier).filter(
                Supplier.is_active == True,
                scope_filter,
            )
            if exclude_ids:
                query = query.filter(Supplier.id.notin_(exclude_ids))

            valid = []
            for supplier in query.all():
                eq_query = db.query(Equipment).filter(
                    Equipment.supplier_id == supplier.id,
                    Equipment.is_active == True,
                    Equipment.license_plate != None,
                    Equipment.license_plate != '',
                    Equipment.status == 'available',
                )
                if equipment_model_id:
                    model = db.query(EquipmentModel).filter(EquipmentModel.id == equipment_model_id).first()
                    if model:
                        category = db.query(EquipmentCategory).filter(EquipmentCategory.id == model.category_id).first()
                        type_filters = []
                        if category and category.name:
                            type_filters.append(Equipment.equipment_type.ilike(category.name))
                        if category and category.id:
                            type_filters.append(Equipment.category_id == category.id)
                        if type_filters:
                            eq_query = eq_query.filter(or_(*type_filters))
                if eq_query.first():
                    valid.append(supplier)

            if not valid:
                return None

            valid.sort(key=lambda s: s.total_assignments or 0)
            return valid[0]

        # Fallback 1: Try area_id
        if area_id:
            supplier = _find_in_scope(Supplier.active_area_ids.contains([area_id]))
            if supplier:
                supplier.total_assignments = (supplier.total_assignments or 0) + 1
                db.flush()
                return {
                    "supplier_id": supplier.id,
                    "fallback_level": "area",
                    "notify_coordinator": False,
                }

        # Fallback 2: Try region_id
        if region_id:
            supplier = _find_in_scope(Supplier.active_region_ids.contains([region_id]))
            if supplier:
                supplier.total_assignments = (supplier.total_assignments or 0) + 1
                db.flush()
                return {
                    "supplier_id": supplier.id,
                    "fallback_level": "region",
                    "notify_coordinator": False,
                }

# Fallback 3: no supplier found notify coordinator
        return {
            "supplier_id": None,
            "fallback_level": "none",
            "notify_coordinator": True,
        }


supplier_rotation_service = SupplierRotationService()
