"""
Suppliers Router
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Annotated, Optional, List

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse, SupplierListResponse, SupplierSearch
from app.services.supplier_service import supplier_service

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=SupplierListResponse)
def list_suppliers(
    filters: Annotated[SupplierSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    require_permission(current_user, "suppliers.list")
    suppliers, total = supplier_service.list_with_filters(db, filters)
    total_pages = (total + filters.page_size - 1) // filters.page_size
    return SupplierListResponse(items=suppliers, total=total, page=filters.page, page_size=filters.page_size, total_pages=total_pages)


@router.get("/active")
def get_active_suppliers(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    equipment_category_id: Optional[int] = Query(None, description="Filter by equipment category ID"),
    category: Optional[int] = Query(None, description="Alias for equipment_category_id"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """Return active suppliers, optionally filtered by equipment category."""
    from sqlalchemy import text as sa_text

    cat_id = equipment_category_id or category

    if cat_id:
        # The frontend sends equipment_types.id, but supplier_equipment links
        # through equipment_models → equipment_categories (different table, different IDs).
        # We resolve by matching either the category ID directly OR by name-based
        # cross-reference between equipment_types and equipment_categories.
        sql = sa_text("""
            SELECT DISTINCT s.id, s.code, s.name, s.contact_name, s.contact_phone,
                   s.contact_email, s.supplier_type, s.rating, s.is_active,
                   s.region_id, s.area_id, s.total_jobs, s.priority_score
            FROM suppliers s
            JOIN supplier_equipment se ON se.supplier_id = s.id
            JOIN equipment_models em ON em.id = se.equipment_model_id
            JOIN equipment_categories ec ON ec.id = em.category_id
            WHERE (
                em.category_id = :cat_id
                OR ec.name IN (
                    SELECT name FROM equipment_types WHERE id = :cat_id
                )
            )
              AND s.is_active = TRUE
              AND s.deleted_at IS NULL
            ORDER BY s.name
            LIMIT :limit OFFSET :offset
        """)
        rows = db.execute(sql, {"cat_id": cat_id, "limit": limit, "offset": (page - 1) * limit}).mappings().all()
    else:
        sql = sa_text("""
            SELECT id, code, name, contact_name, contact_phone,
                   contact_email, supplier_type, rating, is_active,
                   region_id, area_id, total_jobs, priority_score
            FROM suppliers
            WHERE is_active = TRUE AND deleted_at IS NULL
            ORDER BY name
            LIMIT :limit OFFSET :offset
        """)
        rows = db.execute(sql, {"limit": limit, "offset": (page - 1) * limit}).mappings().all()

    return [dict(r) for r in rows]


@router.get("/by-code/{code}", response_model=SupplierResponse)
def get_supplier_by_code(
    code: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    require_permission(current_user, "suppliers.read")
    supplier = supplier_service.get_by_code(db, code)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    require_permission(current_user, "suppliers.read")
    supplier = supplier_service.get_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    supplier_data: SupplierCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    require_permission(current_user, "suppliers.create")
    return supplier_service.create_supplier(db, supplier_data)


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    require_permission(current_user, "suppliers.update")
    return supplier_service.update_supplier(db, supplier_id, supplier_data)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supplier_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    require_permission(current_user, "suppliers.delete")
    supplier_service.soft_delete(db, supplier_id)
    return None


# ── Global supplier equipment list (all suppliers) ────────────────────────────
from app.models.supplier_equipment import SupplierEquipment
from app.models.supplier import Supplier as SupplierModel
from app.models.equipment_model import EquipmentModel


@router.get("-equipment", tags=["suppliers"])
def list_all_supplier_equipment(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Return all supplier_equipment rows enriched with supplier/model names."""
    require_permission(current_user, "suppliers.read")
    rows = (
        db.query(SupplierEquipment, SupplierModel, EquipmentModel)
        .join(SupplierModel, SupplierModel.id == SupplierEquipment.supplier_id, isouter=True)
        .join(EquipmentModel, EquipmentModel.id == SupplierEquipment.equipment_model_id, isouter=True)
        .filter(SupplierEquipment.is_active == True)
        .all()
    )
    return [
        {
            "id": se.id,
            "supplier_id": se.supplier_id,
            "supplier_name": s.name if s else None,
            "equipment_model_id": se.equipment_model_id,
            "equipment_name": em.name if em else None,
            "license_plate": se.license_plate,
            "status": se.status,
            "hourly_rate": float(se.hourly_rate) if se.hourly_rate else None,
            "is_active": se.is_active,
            # alias fields expected by frontend
            "base_rate": float(se.hourly_rate) if se.hourly_rate else None,
            "night_rate": None,
            "weekend_rate": None,
        }
        for se, s, em in rows
    ]


@router.get("/{supplier_id}/equipment", tags=["suppliers"])
def list_supplier_equipment(
    supplier_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Return equipment for a specific supplier."""
    require_permission(current_user, "suppliers.read")
    rows = (
        db.query(SupplierEquipment, EquipmentModel)
        .join(EquipmentModel, EquipmentModel.id == SupplierEquipment.equipment_model_id, isouter=True)
        .filter(SupplierEquipment.supplier_id == supplier_id, SupplierEquipment.is_active == True)
        .all()
    )
    return [
        {
            "id": se.id,
            "supplier_id": se.supplier_id,
            "equipment_model_id": se.equipment_model_id,
            "equipment_name": em.name if em else None,
            "license_plate": se.license_plate,
            "status": se.status,
            "hourly_rate": float(se.hourly_rate) if se.hourly_rate else None,
            "is_active": se.is_active,
        }
        for se, em in rows
    ]
