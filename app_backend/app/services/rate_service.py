"""
Rate Service — מקור תעריף אחד רשמי.

מקור האמת הוא מודול הספקים:
- ציוד ספקים (`equipment` עם `supplier_id`)
- סוגי ציוד (`equipment_types`)

כל חישוב מחיר במערכת אמור להישען על הנתונים שמנוהלים שם.
"""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _get_equipment_type_by_name_or_model(
    db: Session,
    equipment_type_id: Optional[int] = None,
    equipment_type_name: Optional[str] = None,
    equipment_model_id: Optional[int] = None,
):
    from app.models.equipment_type import EquipmentType

    if equipment_type_id:
        et = db.query(EquipmentType).filter(EquipmentType.id == equipment_type_id).first()
        if et:
            return et

    if equipment_type_name:
        et = (
            db.query(EquipmentType)
            .filter(EquipmentType.name.ilike(equipment_type_name.strip()))
            .first()
        )
        if et:
            return et

    if equipment_model_id:
        try:
            from app.models.equipment_model import EquipmentModel
            from app.models.equipment_category import EquipmentCategory

            row = (
                db.query(EquipmentType)
                .join(EquipmentCategory, EquipmentCategory.id == EquipmentType.category_id)
                .join(EquipmentModel, EquipmentModel.category_id == EquipmentCategory.id)
                .filter(EquipmentModel.id == equipment_model_id)
                .first()
            )
            if row:
                return row
        except Exception as exc:
            logger.debug(f"equipment_model -> equipment_type lookup failed: {exc}")

    return None


def resolve_supplier_pricing(
    db: Session,
    supplier_id: Optional[int] = None,
    equipment_id: Optional[int] = None,
    license_plate: Optional[str] = None,
    equipment_type_id: Optional[int] = None,
    equipment_type_name: Optional[str] = None,
    equipment_model_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Resolve pricing from the supplier settings source of truth.

    Priority:
      1. Exact supplier equipment (`equipment`) match
      2. Supplier equipment by requested type/name
      3. Equipment type default (`equipment_types`)
    """
    from app.models.equipment import Equipment

    equipment_type = _get_equipment_type_by_name_or_model(
        db,
        equipment_type_id=equipment_type_id,
        equipment_type_name=equipment_type_name,
        equipment_model_id=equipment_model_id,
    )

    hourly: float = 0.0
    overnight: float = 0.0
    source: str = "none"
    source_name: str = "לא הוגדר"
    matched_equipment_id: Optional[int] = None

    exact_equipment = None
    if equipment_id:
        exact_equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    elif supplier_id and license_plate:
        exact_equipment = (
            db.query(Equipment)
            .filter(
                Equipment.supplier_id == supplier_id,
                Equipment.license_plate == license_plate,
                Equipment.is_active == True,
            )
            .first()
        )

    if exact_equipment:
        matched_equipment_id = exact_equipment.id
        if exact_equipment.hourly_rate and float(exact_equipment.hourly_rate) > 0:
            hourly = float(exact_equipment.hourly_rate)
            source = "supplier_equipment"
            source_name = exact_equipment.license_plate or exact_equipment.name or "ציוד ספק"
        if exact_equipment.overnight_rate and float(exact_equipment.overnight_rate) > 0:
            overnight = float(exact_equipment.overnight_rate)
        if not hourly and exact_equipment.type_id:
            equipment_type = _get_equipment_type_by_name_or_model(db, equipment_type_id=exact_equipment.type_id)

    if not hourly and supplier_id:
        supplier_equipment_query = db.query(Equipment).filter(
            Equipment.supplier_id == supplier_id,
            Equipment.is_active == True,
            Equipment.license_plate.isnot(None),
            Equipment.license_plate != "",
        )

        type_filters = []
        if equipment_type_id:
            type_filters.append(Equipment.type_id == equipment_type_id)
        if equipment_type_name:
            type_filters.append(Equipment.equipment_type.ilike(equipment_type_name.strip()))
        if equipment_type and equipment_type.id:
            type_filters.append(Equipment.type_id == equipment_type.id)
            type_filters.append(Equipment.equipment_type.ilike(equipment_type.name))
        if type_filters:
            supplier_equipment_query = supplier_equipment_query.filter(or_(*type_filters))

        supplier_equipment = (
            supplier_equipment_query
            .order_by(Equipment.hourly_rate.desc().nullslast(), Equipment.id.asc())
            .first()
        )

        if supplier_equipment:
            matched_equipment_id = supplier_equipment.id
            if supplier_equipment.hourly_rate and float(supplier_equipment.hourly_rate) > 0:
                hourly = float(supplier_equipment.hourly_rate)
                source = "supplier_equipment"
                source_name = supplier_equipment.license_plate or supplier_equipment.name or "ציוד ספק"
            if supplier_equipment.overnight_rate and float(supplier_equipment.overnight_rate) > 0:
                overnight = float(supplier_equipment.overnight_rate)
            if not equipment_type and supplier_equipment.type_id:
                equipment_type = _get_equipment_type_by_name_or_model(
                    db,
                    equipment_type_id=supplier_equipment.type_id,
                )

    if equipment_type:
        if not hourly:
            type_rate = getattr(equipment_type, "hourly_rate", None) or getattr(equipment_type, "default_hourly_rate", None)
            if type_rate and float(type_rate) > 0:
                hourly = float(type_rate)
                source = "equipment_type"
                source_name = equipment_type.name or "סוג ציוד"
        if not overnight:
            overnight_rate = getattr(equipment_type, "overnight_rate", None)
            if overnight_rate and float(overnight_rate) > 0:
                overnight = float(overnight_rate)

    return {
        "hourly_rate": hourly,
        "overnight_rate": overnight,
        "source": source,
        "source_name": source_name,
        "equipment_id": matched_equipment_id,
    }


def get_equipment_rate(
    equipment_id: int,
    supplier_id: Optional[int],
    db: Session,
) -> Dict[str, Any]:
    """
    Returns: {"hourly_rate": float, "overnight_rate": float, "source": str}
    """
    result = resolve_supplier_pricing(
        db=db,
        supplier_id=supplier_id,
        equipment_id=equipment_id,
    )
    logger.debug(
        f"get_equipment_rate equipment_id={equipment_id} supplier_id={supplier_id} "
        f"hourly={result['hourly_rate']} overnight={result['overnight_rate']} source={result['source']}"
    )
    return {
        "hourly_rate": result["hourly_rate"],
        "overnight_rate": result["overnight_rate"],
        "source": result["source"],
    }


def get_equipment_rate_by_work_order(work_order_id: int, db: Session) -> Dict[str, Any]:
    """Convenience wrapper — looks up equipment + supplier from the work order."""
    from app.models.work_order import WorkOrder
    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        return {"hourly_rate": 0.0, "overnight_rate": 0.0, "source": "none"}
    result = resolve_supplier_pricing(
        db=db,
        supplier_id=wo.supplier_id,
        equipment_id=wo.equipment_id,
        license_plate=wo.equipment_license_plate,
        equipment_type_name=wo.equipment_type,
        equipment_model_id=getattr(wo, "requested_equipment_model_id", None),
    )
    return {
        "hourly_rate": result["hourly_rate"],
        "overnight_rate": result["overnight_rate"],
        "source": result["source"],
    }


# Legacy class API (backwards-compatible) 

VAT_RATE = 0.18


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
