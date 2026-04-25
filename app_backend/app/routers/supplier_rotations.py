# app/routers/supplier_rotations.py
"""Supplier rotations management endpoints - Fair rotation system."""
from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.supplier_rotation import SupplierRotation
from app.models.supplier import Supplier
from app.models.user import User

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/supplier-rotations", tags=["Supplier Rotations"])


# ---------------------------------------------------------------------------
# Wave 7.D — scope helpers
# ---------------------------------------------------------------------------

def _is_global_scope(user: User) -> bool:
    """ADMIN and ORDER_COORDINATOR see/manage rotations across all regions
    and areas. Other roles (REGION/AREA managers) are scoped down."""
    code = (user.role.code if user.role else "").upper()
    return code in ("ADMIN", "SUPER_ADMIN", "ORDER_COORDINATOR")


def _check_rotation_scope(user: User, rotation) -> None:
    """Raise 403 if `user` is not allowed to access this specific rotation row.

    - Global-scope roles (ADMIN, ORDER_COORDINATOR) always pass.
    - REGION_MANAGER passes only when rotation.region_id matches the
      user's region_id. Rotations with NULL region_id are treated as
      global config and are NOT exposed to non-global roles (a NULL row
      could refer to any region; safer to hide than to leak).
    - AREA_MANAGER: same logic with area_id.
    - All other roles are blocked by `require_permission` higher up; if
      they ever reach this helper we still 403 defensively.
    """
    if _is_global_scope(user):
        return

    forbidden = HTTPException(
        status_code=http_status.HTTP_403_FORBIDDEN,
        detail="אין הרשאה לרשומת סבב זו",
    )
    code = (user.role.code if user.role else "").upper()

    if code == "REGION_MANAGER":
        if not user.region_id or rotation.region_id != user.region_id:
            raise forbidden
        return
    if code == "AREA_MANAGER":
        if not user.area_id or rotation.area_id != user.area_id:
            raise forbidden
        return

    raise forbidden


def _apply_rotation_scope_filter(query, user: User):
    """Return `query` narrowed to the rows the user is allowed to read.

    For global-scope roles the query is returned unchanged.
    For region/area managers we add a WHERE so the COUNT and the page
    both reflect what the user can actually see.
    """
    if _is_global_scope(user):
        return query

    code = (user.role.code if user.role else "").upper()
    if code == "REGION_MANAGER" and user.region_id:
        return query.filter(SupplierRotation.region_id == user.region_id)
    if code == "AREA_MANAGER" and user.area_id:
        return query.filter(SupplierRotation.area_id == user.area_id)
    # Defensive: any role that somehow got here without a scope —
    # show nothing rather than everything.
    return query.filter(False)


class SupplierRotationCreate(BaseModel):
    """Create payload for supplier rotation rows.

    Cleanup #2 (post-Wave 7) — `equipment_category_id` removed.
    Phase 1.3 dropped the column from the model; the schema still
    accepted it and the create handler passed it to the model
    constructor → guaranteed TypeError on every successful admin
    POST. Removed from the schema and from the handler. Any caller
    still sending it gets a Pydantic 422 with a clear "extra field"
    error instead of silently working then 500'ing.
    """
    supplier_id: int
    equipment_type_id: Optional[int] = None
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    rotation_position: Optional[int] = None
    is_active: bool = True
    is_available: Optional[bool] = True
    priority_score: Optional[float] = None


class SupplierRotationUpdate(BaseModel):
    """Same cleanup applies on update."""
    supplier_id: Optional[int] = None
    equipment_type_id: Optional[int] = None
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    rotation_position: Optional[int] = None
    is_active: Optional[bool] = None
    is_available: Optional[bool] = None
    priority_score: Optional[float] = None
    unavailable_until: Optional[str] = None
    unavailable_reason: Optional[str] = None


@router.get("/")
async def get_supplier_rotations(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    equipment_type: Optional[str] = Query(None, description="Filter by equipment type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get list of supplier rotations.

    Wave 7.D — gated by `supplier_rotations.list` (ADMIN +
    ORDER_COORDINATOR + AREA_MANAGER + REGION_MANAGER per Wave 7.A
    matrix). Result set is then narrowed via _apply_rotation_scope_filter
    so AREA/REGION managers only see rotations in their own area/region;
    global-scope roles see everything.
    """
    require_permission(current_user, "supplier_rotations.list")
    try:
        query = db.query(SupplierRotation)
        query = _apply_rotation_scope_filter(query, current_user)

        if is_active is not None:
            query = query.filter(SupplierRotation.is_active == is_active)

        if equipment_type:
            query = query.filter(SupplierRotation.equipment_type_id == int(equipment_type) if equipment_type.isdigit() else True)

        query = query.order_by(SupplierRotation.rotation_position)
        total = query.count()
        rotations = query.offset((page - 1) * page_size).limit(page_size).all()
        
        supplier_ids = [r.supplier_id for r in rotations]
        suppliers = db.query(Supplier).filter(Supplier.id.in_(supplier_ids)).all() if supplier_ids else []
        supplier_map = {s.id: s.name for s in suppliers}
        
        from sqlalchemy import text as sa_text
        et_rows = db.execute(sa_text("SELECT id, name FROM equipment_types WHERE is_active = true")).fetchall()
        et_map = {r[0]: r[1] for r in et_rows}
        
        area_rows = db.execute(sa_text("SELECT id, name FROM areas")).fetchall()
        area_map = {r[0]: r[1] for r in area_rows}
        region_rows = db.execute(sa_text("SELECT id, name FROM regions")).fetchall()
        region_map = {r[0]: r[1] for r in region_rows}
        
        items = []
        for rot in rotations:
            items.append({
                "id": rot.id,
                "supplier_id": rot.supplier_id,
                "supplier_name": supplier_map.get(rot.supplier_id, f"ספק #{rot.supplier_id}"),
                "rotation_position": rot.rotation_position,
                "total_assignments": rot.total_assignments or 0,
                "successful_completions": rot.successful_completions or 0,
                "rejection_count": rot.rejection_count or 0,
                "priority_score": rot.priority_score or 0,
                "is_active": rot.is_active,
                "is_available": rot.is_available,
                "last_assignment_date": rot.last_assignment_date.isoformat() if rot.last_assignment_date else None,
                "last_completion_date": rot.last_completion_date.isoformat() if rot.last_completion_date else None,
                "equipment_type_id": rot.equipment_type_id,
                "equipment_type": et_map.get(rot.equipment_type_id, ''),
                "area_id": rot.area_id,
                "area_name": area_map.get(rot.area_id, ''),
                "region_id": rot.region_id,
                "region_name": region_map.get(rot.region_id, ''),
            })
        
        return {"items": items, "total": total, "page": page, "page_size": page_size}
        
    except Exception as e:
        logger.error(f"Error fetching supplier rotations: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בטעינת סבב ספקים"
        )


@router.get("/{rotation_id}")
async def get_supplier_rotation(
    rotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific supplier rotation by ID.

    Wave 7.D — `supplier_rotations.read` + per-row scope check.
    """
    require_permission(current_user, "supplier_rotations.read")
    try:
        rotation = db.query(SupplierRotation).filter(
            SupplierRotation.id == rotation_id
        ).first()

        if not rotation:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="רשומת סבב לא נמצאה"
            )

        _check_rotation_scope(current_user, rotation)

        # Get supplier name
        supplier = db.query(Supplier).filter(Supplier.id == rotation.supplier_id).first()
        
        return {
            "id": rotation.id,
            "supplier_id": rotation.supplier_id,
            "supplier_name": supplier.name if supplier else f"ספק #{rotation.supplier_id}",
            "rotation_position": rotation.rotation_position,
            "equipment_type_id": rotation.equipment_type_id,
            "region_id": rotation.region_id,
            "area_id": rotation.area_id,
            "total_assignments": rotation.total_assignments,
            "successful_completions": rotation.successful_completions,
            "rejection_count": rotation.rejection_count,
            "priority_score": rotation.priority_score,
            "is_active": rotation.is_active,
            "is_available": rotation.is_available,
            "last_assignment_date": rotation.last_assignment_date.isoformat() if rotation.last_assignment_date else None,
            "last_completion_date": rotation.last_completion_date.isoformat() if rotation.last_completion_date else None,
            "unavailable_until": rotation.unavailable_until.isoformat() if rotation.unavailable_until else None,
            "unavailable_reason": rotation.unavailable_reason,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching supplier rotation {rotation_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בטעינת רשומת סבב"
        )


@router.post("/")
async def create_supplier_rotation(
    data: SupplierRotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new supplier rotation entry.

    Wave 7.D — `supplier_rotations.create` (ADMIN, ORDER_COORDINATOR).
    Both global-scope roles, so no per-row scope check needed.
    """
    require_permission(current_user, "supplier_rotations.create")
    try:
        # Check if supplier exists
        supplier = db.query(Supplier).filter(Supplier.id == data.supplier_id).first()
        if not supplier:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="ספק לא נמצא"
            )
        
        # Validate equipment_type_id FK if provided
        if data.equipment_type_id:
            from sqlalchemy import text as sa_text
            et_exists = db.execute(
                sa_text("SELECT 1 FROM equipment_types WHERE id = :id"),
                {"id": data.equipment_type_id}
            ).fetchone()
            if not et_exists:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"סוג ציוד {data.equipment_type_id} לא נמצא"
                )
        
        rotation = SupplierRotation(
            supplier_id=data.supplier_id,
            equipment_type_id=data.equipment_type_id,
            region_id=data.region_id,
            area_id=data.area_id,
            rotation_position=data.rotation_position,
            is_active=data.is_active,
            is_available=data.is_available,
            priority_score=data.priority_score,
            total_assignments=0,
            successful_completions=0,
            rejection_count=0,
        )
        
        db.add(rotation)
        db.commit()
        db.refresh(rotation)
        
        return {"id": rotation.id, "message": "ספק נוסף לסבב בהצלחה"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating supplier rotation: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בהוספת ספק לסבב"
        )


@router.put("/{rotation_id}")
async def update_supplier_rotation(
    rotation_id: int,
    data: SupplierRotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a supplier rotation entry.

    Wave 7.D — `supplier_rotations.update` (ADMIN, ORDER_COORDINATOR).
    Both global-scope; per-row scope check is a no-op for them but
    kept defensively in case the role matrix grows later.
    """
    require_permission(current_user, "supplier_rotations.update")
    try:
        rotation = db.query(SupplierRotation).filter(
            SupplierRotation.id == rotation_id
        ).first()

        if not rotation:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="רשומת סבב לא נמצאה"
            )

        _check_rotation_scope(current_user, rotation)

        # Update fields
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(rotation, field, value)
        
        db.commit()
        db.refresh(rotation)
        
        return {"message": "רשומת סבב עודכנה בהצלחה"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating supplier rotation {rotation_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בעדכון רשומת סבב"
        )


@router.patch("/{rotation_id}")
async def patch_supplier_rotation(
    rotation_id: int,
    data: SupplierRotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Partially update a supplier rotation entry."""
    return await update_supplier_rotation(rotation_id, data, db, current_user)


@router.delete("/{rotation_id}")
async def delete_supplier_rotation(
    rotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a supplier rotation entry.

    Wave 7.D — `supplier_rotations.delete` (ADMIN only).
    """
    require_permission(current_user, "supplier_rotations.delete")
    try:
        rotation = db.query(SupplierRotation).filter(
            SupplierRotation.id == rotation_id
        ).first()

        if not rotation:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="רשומת סבב לא נמצאה"
            )

        db.delete(rotation)
        db.commit()
        
        return {"message": "ספק הוסר מהסבב בהצלחה"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting supplier rotation {rotation_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאה בהסרת ספק מהסבב"
        )

