#!/usr/bin/env python3
"""
Sync supplier_equipment rows from equipment rows.

Purpose:
- Keep legacy `supplier_equipment` aligned with the current source-of-truth
  used by Supplier Settings (`equipment` rows with `supplier_id`).
- Fill missing supplier_equipment rows by license plate.
- Update pricing/status fields to reflect equipment values.

Usage:
  cd app_backend
  set -a && . .env && set +a
  python3 scripts/sync_supplier_equipment_from_equipment.py --dry-run
  python3 scripts/sync_supplier_equipment_from_equipment.py --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func

from app.core.database import SessionLocal
from app.models.equipment import Equipment
from app.models.equipment_category import EquipmentCategory
from app.models.equipment_model import EquipmentModel
from app.models.equipment_type import EquipmentType
from app.models.supplier_equipment import SupplierEquipment


def resolve_category_and_model_id(db, equipment: Equipment) -> tuple[int | None, int | None]:
    type_obj = None
    if equipment.type_id:
        type_obj = db.query(EquipmentType).filter(EquipmentType.id == equipment.type_id).first()

    category = None
    if type_obj and getattr(type_obj, "category_id", None):
        category = db.query(EquipmentCategory).filter(
            EquipmentCategory.id == type_obj.category_id
        ).first()

    type_name = equipment.equipment_type or (type_obj.name if type_obj else None)
    if not category and type_name:
        category = db.query(EquipmentCategory).filter(
            func.lower(EquipmentCategory.name) == func.lower(type_name)
        ).first()

    if not category:
        return equipment.category_id, None

    model = (
        db.query(EquipmentModel)
        .filter(
            EquipmentModel.category_id == category.id,
            EquipmentModel.is_active == True,
        )
        .order_by(EquipmentModel.id.asc())
        .first()
    )
    return category.id, model.id if model else None


def sync(apply: bool = False) -> int:
    db = SessionLocal()
    changes = 0
    try:
        equipment_rows = (
            db.query(Equipment)
            .filter(
                Equipment.supplier_id.isnot(None),
                Equipment.license_plate.isnot(None),
                Equipment.license_plate != "",
            )
            .order_by(Equipment.id.asc())
            .all()
        )

        print(f"Found {len(equipment_rows)} equipment rows to inspect")

        for eq in equipment_rows:
            category_id, model_id = resolve_category_and_model_id(db, eq)
            se = (
                db.query(SupplierEquipment)
                .filter(
                    SupplierEquipment.supplier_id == eq.supplier_id,
                    func.upper(SupplierEquipment.license_plate) == eq.license_plate.upper(),
                )
                .first()
            )

            before = None
            if se:
                before = (
                    se.equipment_category_id,
                    se.equipment_model_id,
                    se.status,
                    float(se.hourly_rate or 0),
                    se.quantity_available,
                    se.is_active,
                )
            else:
                se = SupplierEquipment(
                    supplier_id=eq.supplier_id,
                    license_plate=eq.license_plate,
                )
                db.add(se)

            se.equipment_category_id = category_id
            if model_id:
                se.equipment_model_id = model_id
            se.status = eq.status or se.status or "available"
            se.hourly_rate = eq.hourly_rate
            se.quantity_available = 1 if eq.is_active else 0
            se.is_active = bool(eq.is_active)

            after = (
                se.equipment_category_id,
                se.equipment_model_id,
                se.status,
                float(se.hourly_rate or 0),
                se.quantity_available,
                se.is_active,
            )

            if before != after:
                changes += 1
                print(
                    f"[CHANGE] equipment #{eq.id} plate={eq.license_plate} supplier={eq.supplier_id} "
                    f"-> category={category_id} model={model_id} status={se.status} "
                    f"hourly_rate={float(eq.hourly_rate or 0)} is_active={eq.is_active}"
                )

        if apply:
            db.commit()
            print(f"\nApplied {changes} supplier_equipment sync changes.")
        else:
            db.rollback()
            print(f"\nDry run complete. {changes} changes would be applied.")

        return changes
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync supplier_equipment from equipment")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes only")
    args = parser.parse_args()

    apply = args.apply and not args.dry_run
    sync(apply=apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
