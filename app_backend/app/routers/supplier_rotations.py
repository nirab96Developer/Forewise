# app/routers/supplier_rotations.py
"""Supplier rotations management endpoints - Fair rotation system."""
from typing import List, Optional
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.supplier_rotation import SupplierRotation
from app.models.supplier import Supplier
from app.models.user import User

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/supplier-rotations", tags=["Supplier Rotations"])


class SupplierRotationCreate(BaseModel):
    supplier_id: int
    equipment_type_id: Optional[int] = None
    equipment_category_id: Optional[int] = None
    region_id: Optional[int] = None
    area_id: Optional[int] = None
    rotation_position: Optional[int] = None
    is_active: bool = True
    is_available: Optional[bool] = True
    priority_score: Optional[float] = None


class SupplierRotationUpdate(BaseModel):
    supplier_id: Optional[int] = None
    equipment_type_id: Optional[int] = None
    equipment_category_id: Optional[int] = None
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get list of supplier rotations."""
    try:
        query = db.query(SupplierRotation)
        
        if is_active is not None:
            query = query.filter(SupplierRotation.is_active == is_active)
        
        if equipment_type:
            query = query.filter(SupplierRotation.equipment_type_id == int(equipment_type) if equipment_type.isdigit() else True)
        
        rotations = query.order_by(SupplierRotation.rotation_position).all()
        
        # Get supplier names
        supplier_ids = [r.supplier_id for r in rotations]
        suppliers = db.query(Supplier).filter(Supplier.id.in_(supplier_ids)).all()
        supplier_map = {s.id: s.name for s in suppliers}
        
        result = []
        for rot in rotations:
            result.append({
                "id": rot.id,
                "supplier_id": rot.supplier_id,
                "supplier_name": supplier_map.get(rot.supplier_id, f"ספק #{rot.supplier_id}"),
                "rotation_position": rot.rotation_position,
                "total_assignments": rot.total_assignments,
                "successful_completions": rot.successful_completions,
                "rejection_count": rot.rejection_count,
                "priority_score": rot.priority_score,
                "is_active": rot.is_active,
                "is_available": rot.is_available,
                "last_assignment_date": rot.last_assignment_date.isoformat() if rot.last_assignment_date else None,
                "last_completion_date": rot.last_completion_date.isoformat() if rot.last_completion_date else None,
                "equipment_type_id": rot.equipment_type_id,
                "equipment_category_id": rot.equipment_category_id,
            })
        
        return result
        
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
    """Get a specific supplier rotation by ID."""
    try:
        rotation = db.query(SupplierRotation).filter(
            SupplierRotation.id == rotation_id
        ).first()
        
        if not rotation:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="רשומת סבב לא נמצאה"
            )
        
        # Get supplier name
        supplier = db.query(Supplier).filter(Supplier.id == rotation.supplier_id).first()
        
        return {
            "id": rotation.id,
            "supplier_id": rotation.supplier_id,
            "supplier_name": supplier.name if supplier else f"ספק #{rotation.supplier_id}",
            "rotation_position": rotation.rotation_position,
            "equipment_type_id": rotation.equipment_type_id,
            "equipment_category_id": rotation.equipment_category_id,
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
    """Create a new supplier rotation entry."""
    try:
        # Check if supplier exists
        supplier = db.query(Supplier).filter(Supplier.id == data.supplier_id).first()
        if not supplier:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="ספק לא נמצא"
            )
        
        rotation = SupplierRotation(
            supplier_id=data.supplier_id,
            equipment_type_id=data.equipment_type_id,
            equipment_category_id=data.equipment_category_id,
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
    """Update a supplier rotation entry."""
    try:
        rotation = db.query(SupplierRotation).filter(
            SupplierRotation.id == rotation_id
        ).first()
        
        if not rotation:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="רשומת סבב לא נמצאה"
            )
        
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
    """Delete a supplier rotation entry."""
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

