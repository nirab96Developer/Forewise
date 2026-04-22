"""Equipment Models endpoints — small read-only router used by the
coordinator screen to resolve equipment_model_id → display name."""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.equipment_model import EquipmentModel

router = APIRouter(prefix="/equipment-models", tags=["Equipment Models"])


@router.get("/active")
def list_active_equipment_models(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    category_id: Optional[int] = Query(None, description="Filter by equipment category"),
):
    """Return all active equipment models, optionally filtered by category.

    Shape is intentionally lean — the FE only needs id/name/category_id
    to build a lookup map for display.
    """
    q = db.query(EquipmentModel).filter(EquipmentModel.is_active == True)
    if category_id is not None:
        q = q.filter(EquipmentModel.category_id == category_id)
    rows = q.order_by(EquipmentModel.name.asc()).all()
    return {
        "items": [
            {"id": m.id, "name": m.name, "category_id": m.category_id}
            for m in rows
        ],
        "total": len(rows),
    }


@router.get("")
def list_equipment_models(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    is_active: Optional[bool] = Query(None),
    category_id: Optional[int] = Query(None),
):
    """List all equipment models (admin/management views)."""
    q = db.query(EquipmentModel)
    if is_active is not None:
        q = q.filter(EquipmentModel.is_active == is_active)
    if category_id is not None:
        q = q.filter(EquipmentModel.category_id == category_id)
    rows = q.order_by(EquipmentModel.name.asc()).all()
    return {
        "items": [
            {
                "id": m.id,
                "name": m.name,
                "category_id": m.category_id,
                "is_active": m.is_active,
            }
            for m in rows
        ],
        "total": len(rows),
    }
