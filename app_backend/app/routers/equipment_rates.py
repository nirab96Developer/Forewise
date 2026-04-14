"""
Equipment Rates Router — /settings/equipment-rates
Manage hourly rates per equipment type with change history.
"""

from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User

router = APIRouter(prefix="/settings/equipment-rates", tags=["Equipment Rates"])


# Schemas 

class EquipmentRateItem(BaseModel):
    id: int
    name: str
    hourly_rate: Optional[float] = None
    last_updated: Optional[str] = None
    updated_by: Optional[str] = None
    is_active: bool = True


class EquipmentRateCreate(BaseModel):
    name: str = Field(..., min_length=2)
    hourly_rate: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None


class EquipmentRateUpdate(BaseModel):
    hourly_rate: float = Field(..., ge=0)
    reason: Optional[str] = Field(None, min_length=3)


class RateHistoryItem(BaseModel):
    id: int
    old_rate: Optional[float]
    new_rate: Optional[float]
    changed_by_name: Optional[str]
    reason: Optional[str]
    effective_date: Optional[str]
    created_at: str


# Endpoints 

@router.get("", response_model=List[EquipmentRateItem])
def get_equipment_rates(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """List all equipment types with their current hourly rate."""
    require_permission(current_user, "equipment.view")

    rows = db.execute(text("""
        SELECT et.id, et.name, et.default_hourly_rate, et.is_active,
               erh.created_at as last_updated,
               u.full_name as updated_by
        FROM equipment_types et
        LEFT JOIN LATERAL (
            SELECT erh2.created_at, erh2.changed_by
            FROM equipment_rate_history erh2
            WHERE erh2.equipment_type_id = et.id
            ORDER BY erh2.created_at DESC LIMIT 1
        ) erh ON true
        LEFT JOIN users u ON u.id = erh.changed_by
        WHERE et.is_active = true
        ORDER BY et.sort_order NULLS LAST, et.name
    """)).fetchall()

    result = []
    for r in rows:
        result.append(EquipmentRateItem(
            id=r.id,
            name=r.name,
            hourly_rate=float(r.default_hourly_rate) if r.default_hourly_rate is not None else None,
            last_updated=r.last_updated.isoformat() if r.last_updated else None,
            updated_by=r.updated_by,
            is_active=r.is_active,
        ))
    return result


@router.post("", response_model=EquipmentRateItem, status_code=status.HTTP_201_CREATED)
def create_equipment_type(
    data: EquipmentRateCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Add a new equipment type with optional hourly rate."""
    require_permission(current_user, "equipment.manage")

    existing = db.execute(text(
        "SELECT id FROM equipment_types WHERE name = :name AND is_active = true"
    ), {"name": data.name}).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"סוג ציוד '{data.name}' כבר קיים")

    row = db.execute(text("""
        INSERT INTO equipment_types (name, default_hourly_rate, is_active, created_at, updated_at)
        VALUES (:name, :rate, true, NOW(), NOW())
        RETURNING id, name, default_hourly_rate, is_active
    """), {"name": data.name, "rate": data.hourly_rate}).first()
    db.commit()

    # Audit log
    try:
        import json
        db.execute(text("""
            INSERT INTO audit_logs (user_id, table_name, record_id, action, new_values)
            VALUES (:uid, 'equipment_types', :rid, 'CREATE', :nv::jsonb)
        """), {"uid": current_user.id, "rid": row.id,
               "nv": json.dumps({"name": data.name, "hourly_rate": data.hourly_rate})})
        db.commit()
    except Exception:
        pass

    return EquipmentRateItem(
        id=row.id,
        name=row.name,
        hourly_rate=float(row.default_hourly_rate) if row.default_hourly_rate is not None else None,
        is_active=row.is_active,
    )


@router.patch("/{type_id}")
def update_equipment_rate(
    type_id: int,
    data: EquipmentRateUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Update hourly rate for an equipment type and record history."""
    require_permission(current_user, "equipment.manage")

    et_row = db.execute(text(
        "SELECT id, name, default_hourly_rate FROM equipment_types WHERE id=:tid AND is_active=true"
    ), {"tid": type_id}).first()
    if not et_row:
        raise HTTPException(status_code=404, detail="סוג ציוד לא נמצא")

    old_rate = float(et_row.default_hourly_rate) if et_row.default_hourly_rate is not None else None

    # Record history
    db.execute(text("""
        INSERT INTO equipment_rate_history (equipment_type_id, old_rate, new_rate, changed_by, reason, effective_date)
        VALUES (:tid, :old, :new, :uid, :reason, CURRENT_DATE)
    """), {"tid": type_id, "old": old_rate, "new": data.hourly_rate,
           "uid": current_user.id, "reason": data.reason})

    # Update equipment_types
    db.execute(text("""
        UPDATE equipment_types SET default_hourly_rate=:rate, updated_at=NOW() WHERE id=:tid
    """), {"rate": data.hourly_rate, "tid": type_id})

    db.commit()

    return {"success": True, "old_rate": old_rate, "new_rate": data.hourly_rate}


@router.get("/{type_id}/history", response_model=List[RateHistoryItem])
def get_rate_history(
    type_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Return rate change history for a specific equipment type."""
    require_permission(current_user, "equipment.view")

    rows = db.execute(text("""
        SELECT h.id, h.old_rate, h.new_rate, h.reason,
               h.effective_date, h.created_at,
               u.full_name as changed_by_name
        FROM equipment_rate_history h
        LEFT JOIN users u ON u.id = h.changed_by
        WHERE h.equipment_type_id = :tid
        ORDER BY h.created_at DESC
    """), {"tid": type_id}).fetchall()

    return [
        RateHistoryItem(
            id=r.id,
            old_rate=float(r.old_rate) if r.old_rate is not None else None,
            new_rate=float(r.new_rate) if r.new_rate is not None else None,
            changed_by_name=r.changed_by_name,
            reason=r.reason,
            effective_date=r.effective_date.isoformat() if r.effective_date else None,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]
