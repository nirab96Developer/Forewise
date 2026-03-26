"""
Rate Service — מקור תעריף אחד רשמי.

עדיפות:
  1. supplier_equipment.hourly_rate  (ספציפי לספק-ציוד)
  2. equipment.hourly_rate            (ספציפי לציוד)
  3. equipment_types.hourly_rate      (ברירת מחדל לסוג ציוד)

overnight_rate — עדיפות:
  1. equipment_types.overnight_rate
  2. 0 (לא מוגדר)
"""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_equipment_rate(
    equipment_id: int,
    supplier_id: Optional[int],
    db: Session,
) -> Dict[str, Any]:
    """
    Returns: {"hourly_rate": float, "overnight_rate": float, "source": str}
    """
    from app.models.equipment import Equipment
    from app.models.equipment_type import EquipmentType

    hourly: float = 0.0
    overnight: float = 0.0
    source: str = "none"

    # 1. supplier_equipment
    if supplier_id:
        try:
            from app.models.supplier_equipment import SupplierEquipment
            se = (
                db.query(SupplierEquipment)
                .filter(
                    SupplierEquipment.equipment_id == equipment_id,
                    SupplierEquipment.supplier_id == supplier_id,
                    SupplierEquipment.is_active == True,
                )
                .first()
            )
            if se and se.hourly_rate and float(se.hourly_rate) > 0:
                hourly = float(se.hourly_rate)
                source = "supplier_equipment"
        except Exception as e:
            logger.debug(f"supplier_equipment rate lookup failed: {e}")

    # 2. equipment.hourly_rate
    eq = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not eq:
        return {"hourly_rate": hourly, "overnight_rate": overnight, "source": source}

    if not hourly and eq.hourly_rate and float(eq.hourly_rate) > 0:
        hourly = float(eq.hourly_rate)
        source = "equipment"

    # 3. equipment_types fallback
    if eq.equipment_type_id:
        try:
            et = db.query(EquipmentType).filter(EquipmentType.id == eq.equipment_type_id).first()
            if et:
                if not hourly and et.hourly_rate and float(et.hourly_rate) > 0:
                    hourly = float(et.hourly_rate)
                    source = "equipment_type"
                if et.overnight_rate and float(et.overnight_rate) > 0:
                    overnight = float(et.overnight_rate)
        except Exception as e:
            logger.debug(f"equipment_type rate lookup failed: {e}")

    logger.debug(
        f"get_equipment_rate equipment_id={equipment_id} supplier_id={supplier_id} "
f" hourly={hourly} overnight={overnight} source={source}"
    )
    return {"hourly_rate": hourly, "overnight_rate": overnight, "source": source}


def get_equipment_rate_by_work_order(work_order_id: int, db: Session) -> Dict[str, Any]:
    """Convenience wrapper — looks up equipment + supplier from the work order."""
    from app.models.work_order import WorkOrder
    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        return {"hourly_rate": 0.0, "overnight_rate": 0.0, "source": "none"}
    return get_equipment_rate(
        equipment_id=wo.equipment_id,
        supplier_id=wo.supplier_id,
        db=db,
    )


# Legacy class API (backwards-compatible) 

VAT_RATE = 0.17


class _ResolvedRate:
    """Simple container returned by resolve_rate()."""
    def __init__(self, hourly_rate: float, source: str, source_name: str):
        self.hourly_rate = hourly_rate
        self.source = source
        self.source_name = source_name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hourly_rate": self.hourly_rate,
            "rate_source": self.source,
            "rate_source_name": self.source_name,
        }


class RateService:
    """
    Rate service bound to a DB session.
    Use get_rate_service(db) to obtain an instance.
    """

    def __init__(self, db: Session):
        self._db = db

# public API used by pricing router 

    def resolve_rate(
        self,
        work_type: str = "fieldwork",
        equipment_type_id: Optional[int] = None,
        equipment_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        project_id: Optional[int] = None,
        for_date=None,
    ) -> _ResolvedRate:
        """Resolve hourly rate with full priority chain."""
        hourly = 0.0
        source = "none"
        source_name = "לא הוגדר"

        if equipment_id:
            result = get_equipment_rate(equipment_id, supplier_id, self._db)
            hourly = result["hourly_rate"]
            source = result["source"]
            source_name = source
        elif equipment_type_id:
            # Fallback via equipment_types.default_hourly_rate
            try:
                from app.models.equipment_type import EquipmentType
                et = self._db.query(EquipmentType).filter(
                    EquipmentType.id == equipment_type_id
                ).first()
                if et:
                    rate_val = getattr(et, "default_hourly_rate", None) or getattr(et, "hourly_rate", None)
                    if rate_val and float(rate_val) > 0:
                        hourly = float(rate_val)
                        source = "equipment_type"
                        source_name = et.name or "סוג ציוד"
            except Exception as exc:
                logger.debug(f"resolve_rate equipment_type fallback failed: {exc}")

        return _ResolvedRate(hourly_rate=hourly, source=source, source_name=source_name)

    def compute_worklog_cost(
        self,
        hours,
        work_type: str = "fieldwork",
        equipment_id: Optional[int] = None,
        equipment_type_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        project_id: Optional[int] = None,
        for_date=None,
        hourly_rate_snapshot: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Compute total cost for a worklog (before and after VAT).

        If neither equipment_id nor hourly_rate_snapshot is available we cannot
        determine a reliable rate — return cost=0 with flag 'missing_rate_source'
        instead of showing a fabricated number.
        """
# Guard: no equipment context AND no stored snapshot cannot price
        if equipment_id is None and equipment_type_id is None and hourly_rate_snapshot is None:
            logger.warning(
                "compute_worklog_cost: equipment_id=None, equipment_type_id=None, "
                "hourly_rate_snapshot=None — returning cost=0 (missing_rate_source)"
            )
            return {
                "hourly_rate": 0.0,
                "total_cost": 0.0,
                "total_cost_with_vat": 0.0,
                "rate_source": "missing_rate_source",
                "rate_source_name": "חסר מקור תעריף",
                "flag": "missing_rate_source",
            }

        # If we have a stored snapshot, prefer it directly (most accurate)
        if hourly_rate_snapshot is not None and hourly_rate_snapshot > 0:
            hourly = float(hourly_rate_snapshot)
            source = "hourly_rate_snapshot"
            source_name = "תעריף שמור בדיווח"
        else:
            resolved = self.resolve_rate(
                work_type=work_type,
                equipment_type_id=equipment_type_id,
                equipment_id=equipment_id,
                supplier_id=supplier_id,
                project_id=project_id,
                for_date=for_date,
            )
            hourly = resolved.hourly_rate
            source = resolved.source
            source_name = resolved.source_name

        try:
            hours_f = float(hours)
        except (TypeError, ValueError):
            hours_f = 0.0

        total = round(hourly * hours_f, 2)
        total_vat = round(total * (1 + VAT_RATE), 2)

        return {
            "hourly_rate": hourly,
            "total_cost": total,
            "total_cost_with_vat": total_vat,
            "rate_source": source,
            "rate_source_name": source_name,
        }

# legacy helpers (kept for backward-compat) 

    def get_equipment_rate_full(
        self,
        equipment_id: int,
        supplier_id: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        return get_equipment_rate(equipment_id, supplier_id, db or self._db)

    def get_equipment_rate(
        self,
        equipment_type_id: int,
        supplier_id: Optional[int] = None,
        project_id: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> float:
        resolved = self.resolve_rate(
            equipment_type_id=equipment_type_id,
            supplier_id=supplier_id,
        )
        return resolved.hourly_rate

    def get_hourly_rate(
        self,
        work_type: str,
        supplier_id: Optional[int] = None,
        project_id: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> float:
        return self.resolve_rate(supplier_id=supplier_id).hourly_rate

    def calculate_worklog_cost(
        self,
        hours: float,
        equipment_type_id: int,
        supplier_id: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> float:
        rate = self.get_equipment_rate(equipment_type_id, supplier_id)
        return hours * rate


def get_rate_service(db: Session) -> RateService:
    """Factory — returns a RateService bound to the given DB session."""
    return RateService(db)
