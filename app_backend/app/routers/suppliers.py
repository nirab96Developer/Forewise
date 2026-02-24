"""
Suppliers Router - API endpoints לספקים
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.models.equipment_model import EquipmentModel
from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierList,
    SupplierSearch,
    SupplierStatistics,
    SupplierEquipmentCreate,
    SupplierEquipmentUpdate,
    SupplierEquipmentResponse,
)
from app.services.supplier_service import SupplierService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])
supplier_service = SupplierService()


@router.get("", response_model=SupplierList)
def list_suppliers(
    search: Annotated[SupplierSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List suppliers - permissions: suppliers.read"""
    require_permission(current_user, "suppliers.read")
    
    try:
        suppliers, total = supplier_service.list(db, search)
        total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
        
        return SupplierList(
            items=suppliers,
            total=total,
            page=search.page,
            page_size=search.page_size,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================
# SPECIFIC ROUTES MUST COME BEFORE /{supplier_id}
# ============================================

@router.get("/active", response_model=list[SupplierResponse])
def get_active_suppliers(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    equipment_category_id: Optional[int] = Query(None, description="Filter by equipment category"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100)
):
    """Get active suppliers - permissions: suppliers.read"""
    require_permission(current_user, "suppliers.read")
    
    try:
        search = SupplierSearch(is_active=True, page=page, page_size=limit)
        suppliers, total = supplier_service.list(db, search)
        return suppliers
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/statistics", response_model=SupplierStatistics)
def get_supplier_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    supplier_type: Optional[str] = Query(None, description="Filter by type")
):
    """Get statistics - permissions: suppliers.read"""
    require_permission(current_user, "suppliers.read")
    
    try:
        filters = {}
        if supplier_type:
            filters['supplier_type'] = supplier_type
        
        stats = supplier_service.get_statistics(db, filters)
        return stats
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/equipment-models/active")
def list_active_equipment_models(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List active equipment models for supplier equipment forms."""
    require_permission(current_user, "suppliers.read")

    try:
        rows = (
            db.query(EquipmentModel)
            .filter(EquipmentModel.is_active == True)
            .order_by(EquipmentModel.name.asc())
            .all()
        )
        return [
            {
                "id": row.id,
                "name": row.name,
                "category_id": row.category_id,
            }
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{supplier_id}/equipment", response_model=list[SupplierEquipmentResponse])
def list_supplier_equipment(
    supplier_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List supplier equipment inventory rows - permissions: suppliers.read"""
    require_permission(current_user, "suppliers.read")

    try:
        rows = supplier_service.list_supplier_equipment(db, supplier_id)
        return rows
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{supplier_id}/equipment", response_model=SupplierEquipmentResponse, status_code=status.HTTP_201_CREATED)
def add_supplier_equipment(
    supplier_id: int,
    data: SupplierEquipmentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Add equipment model + license plate to supplier - permissions: suppliers.update"""
    require_permission(current_user, "suppliers.update")

    try:
        row = supplier_service.add_supplier_equipment(db, supplier_id, data)
        return row
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{supplier_id}/equipment/{supplier_equipment_id}", response_model=SupplierEquipmentResponse)
def update_supplier_equipment(
    supplier_id: int,
    supplier_equipment_id: int,
    data: SupplierEquipmentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update supplier equipment status/availability - permissions: suppliers.update"""
    require_permission(current_user, "suppliers.update")

    try:
        row = supplier_service.update_supplier_equipment(db, supplier_id, supplier_equipment_id, data)
        return row
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/search")
def search_suppliers(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    q: str = Query(..., min_length=1, description="Search query")
):
    """Search suppliers by name/code - permissions: suppliers.read"""
    require_permission(current_user, "suppliers.read")
    
    try:
        search = SupplierSearch(search=q, page=1, page_size=50)
        suppliers, _ = supplier_service.list(db, search)
        return suppliers
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/by-code/{code}", response_model=SupplierResponse)
def get_supplier_by_code(
    code: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get supplier by code - permissions: suppliers.read"""
    require_permission(current_user, "suppliers.read")
    
    try:
        supplier = supplier_service.get_by_code(db, code)
        if not supplier:
            raise NotFoundException(f"Supplier with code '{code}' not found")
        return supplier
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/equipment/{equipment_type}")
def get_suppliers_by_equipment(
    equipment_type: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get suppliers by equipment type - permissions: suppliers.read"""
    require_permission(current_user, "suppliers.read")
    
    try:
        search = SupplierSearch(is_active=True, page=1, page_size=100)
        suppliers, _ = supplier_service.list(db, search)
        return suppliers
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/next/{equipment_type}")
def get_next_supplier(
    equipment_type: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get next supplier in rotation - permissions: suppliers.read"""
    require_permission(current_user, "suppliers.read")
    
    try:
        search = SupplierSearch(is_active=True, page=1, page_size=1)
        suppliers, _ = supplier_service.list(db, search)
        if suppliers:
            return suppliers[0]
        return None
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================
# ROUTES WITH PATH PARAMETERS MUST COME AFTER SPECIFIC ROUTES
# ============================================

@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get supplier by ID - permissions: suppliers.read"""
    require_permission(current_user, "suppliers.read")
    
    try:
        supplier = supplier_service.get_by_id_or_404(db, supplier_id)
        return supplier
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    data: SupplierCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create supplier - permissions: suppliers.create"""
    require_permission(current_user, "suppliers.create")
    
    try:
        supplier = supplier_service.create(db, data, current_user.id)
        return supplier
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update supplier - permissions: suppliers.update"""
    require_permission(current_user, "suppliers.update")
    
    try:
        supplier = supplier_service.update(db, supplier_id, data, current_user.id)
        return supplier
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DuplicateException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supplier_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Delete supplier - permissions: suppliers.delete"""
    require_permission(current_user, "suppliers.delete")
    
    try:
        supplier_service.soft_delete(db, supplier_id, current_user.id)
        return None
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{supplier_id}/restore", response_model=SupplierResponse)
def restore_supplier(
    supplier_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Restore supplier - permissions: suppliers.restore"""
    require_permission(current_user, "suppliers.restore")
    
    try:
        supplier = supplier_service.restore(db, supplier_id, current_user.id)
        return supplier
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{supplier_id}/stats")
def get_supplier_stats(
    supplier_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get statistics for a specific supplier - permissions: suppliers.read"""
    require_permission(current_user, "suppliers.read")
    
    try:
        supplier = supplier_service.get_by_id_or_404(db, supplier_id)
        stats = supplier_service.get_statistics(db, {'supplier_id': supplier_id})
        return stats
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{supplier_id}/rotation", response_model=SupplierResponse)
def update_supplier_rotation(
    supplier_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    order: int = Query(..., description="New rotation order")
):
    """
    Update supplier rotation order
    
    Permissions: suppliers.update
    """
    require_permission(current_user, "suppliers.update")
    
    try:
        # Update supplier with new rotation order
        update_data = SupplierUpdate(rotation_order=order)
        supplier = supplier_service.update(db, supplier_id, update_data, current_user.id)
        return supplier
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
