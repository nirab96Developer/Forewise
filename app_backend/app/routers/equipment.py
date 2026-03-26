"""
Equipment Router - API endpoints לציוד
Handles HTTP requests for equipment management
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.equipment import (
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentResponse,
    EquipmentBrief,
    EquipmentList,
    EquipmentSearch,
    EquipmentStatistics,
    EquipmentAssignRequest
)
from app.services.equipment_service import EquipmentService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

# Create router
router = APIRouter(prefix="/equipment", tags=["Equipment"])

# Service instance
equipment_service = EquipmentService()


@router.get("")
def list_equipment(
    search: Annotated[EquipmentSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    List equipment with filters and pagination
    
    Permissions: equipment.read
    Returns: Equipment list with supplier_name
    """
    from app.models.supplier import Supplier
    
    # Check permission
    require_permission(current_user, "equipment.read")
    
    try:
        # Default: show only active equipment
        if search.is_active is None:
            search.is_active = True
        # Get list from service
        equipment_list, total = equipment_service.list(db, search)
        
        # Calculate total pages
        total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
        
        # Get supplier names
        supplier_ids = set(eq.supplier_id for eq in equipment_list if eq.supplier_id)
        suppliers = {}
        if supplier_ids:
            supplier_rows = db.query(Supplier.id, Supplier.name).filter(Supplier.id.in_(supplier_ids)).all()
            suppliers = {s.id: s.name for s in supplier_rows}
        
        # Get scan data for today (batch query)
        from sqlalchemy import text as sa_text
        from datetime import date as date_type
        today = date_type.today()
        
        eq_ids = [eq.id for eq in equipment_list]
        scan_today_map = {}
        last_scan_map = {}
        if eq_ids:
            try:
                # Today's scans
                today_rows = db.execute(sa_text("""
                    SELECT equipment_id, MAX(created_at) as last_scan
                    FROM equipment_scans 
                    WHERE equipment_id = ANY(:ids) AND scan_date = :today AND is_valid = true
                    GROUP BY equipment_id
                """), {"ids": eq_ids, "today": today}).fetchall()
                scan_today_map = {r.equipment_id: True for r in today_rows}
                
                # Last scan ever
                last_rows = db.execute(sa_text("""
                    SELECT equipment_id, MAX(scan_date) as last_date
                    FROM equipment_scans 
                    WHERE equipment_id = ANY(:ids) AND is_valid = true
                    GROUP BY equipment_id
                """), {"ids": eq_ids}).fetchall()
                last_scan_map = {r.equipment_id: str(r.last_date) for r in last_rows}
            except:
                pass
        
        # Get active work order assignments (which project is this equipment on?)
        from app.models.work_order import WorkOrder
        assigned_map = {}
        try:
            wo_rows = db.query(
                WorkOrder.equipment_id, WorkOrder.id, WorkOrder.project_id
            ).filter(
                WorkOrder.equipment_id.in_(eq_ids),
                WorkOrder.status.in_(["ACCEPTED", "IN_PROGRESS"]),
                WorkOrder.is_active == True
            ).all()
            for r in wo_rows:
                assigned_map[r.equipment_id] = {"work_order_id": r.id, "project_id": r.project_id}
        except:
            pass
        
        # Build response with supplier_name + operational badges
        items = []
        for eq in equipment_list:
            assignment = assigned_map.get(eq.id)
            item = {
                "id": eq.id,
                "code": eq.code,
                "name": eq.name,
                "license_plate": getattr(eq, 'license_plate', None),
                "equipment_type": getattr(eq, 'equipment_type', None),
                "supplier_id": eq.supplier_id,
                "supplier_name": suppliers.get(eq.supplier_id) if eq.supplier_id else None,
                "hourly_rate": float(eq.hourly_rate) if eq.hourly_rate else None,
                "daily_rate": float(eq.daily_rate) if getattr(eq, 'daily_rate', None) else None,
                "overnight_rate": float(eq.overnight_rate) if getattr(eq, 'overnight_rate', None) else None,
                "night_guard": bool(getattr(eq, 'night_guard', False)),
                "status": eq.status,
                "is_active": eq.is_active,
                # Operational badges
                "scanned_today": scan_today_map.get(eq.id, False),
                "last_scan_date": last_scan_map.get(eq.id),
                "assigned_work_order_id": assignment["work_order_id"] if assignment else None,
                "assigned_project_id": assignment["project_id"] if assignment else None,
            }
            items.append(item)
        
        return {
            "items": items,
            "total": total,
            "page": search.page,
            "page_size": search.page_size,
            "total_pages": total_pages
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


# ============================================
# SPECIFIC ROUTES MUST COME BEFORE /{equipment_id}
# ============================================

@router.get("/statistics", response_model=EquipmentStatistics)
def get_equipment_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    type_id: Optional[int] = Query(None, description="Filter by type"),
    category_id: Optional[int] = Query(None, description="Filter by category")
):
    """
    Get equipment statistics
    
    Permissions: equipment.read
    """
    # Check permission
    require_permission(current_user, "equipment.read")
    
    try:
        filters = {}
        if type_id:
            filters['type_id'] = type_id
        if category_id:
            filters['category_id'] = category_id
        
        stats = equipment_service.get_statistics(db, filters)
        return stats
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.get("/active")
def get_active_equipment(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get all active equipment
    
    Permissions: equipment.read
    """
    require_permission(current_user, "equipment.read")
    
    try:
        search = EquipmentSearch(is_active=True, page=1, page_size=200)
        equipment_list, _ = equipment_service.list(db, search)
        return equipment_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.get("/maintenance-needed")
def get_equipment_needing_maintenance(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get equipment that needs maintenance
    
    Permissions: equipment.read
    """
    require_permission(current_user, "equipment.read")
    
    try:
        # Get equipment with needs_maintenance filter (if available in search)
        search = EquipmentSearch(is_active=True, page=1, page_size=100)
        equipment_list, _ = equipment_service.list(db, search)
        
        # Filter for those needing maintenance
        # This is a simplified implementation - enhance based on actual maintenance fields
        return equipment_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.get("/types/list")
def get_equipment_types_list(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get equipment types for dropdown lists
    Redirects to equipment-types endpoint
    
    Permissions: equipment.read
    """
    require_permission(current_user, "equipment.read")
    
    try:
        from app.services.equipment_type_service import EquipmentTypeService
        from app.schemas.equipment_type import EquipmentTypeSearch
        
        et_service = EquipmentTypeService()
        search = EquipmentTypeSearch(is_active=True, page=1, page_size=100)
        types, _ = et_service.list(db, search)
        return types
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


# ============================================
# BY-CODE AND SCAN ROUTES
# ============================================

@router.get("/by-code/{code}")
def get_equipment_by_code(
    code: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get equipment by code (for QR scanning)
    
    Permissions: equipment.read
    Returns: Equipment with supplier_name
    """
    require_permission(current_user, "equipment.read")
    
    from app.models.equipment import Equipment
    from app.models.supplier import Supplier
    
    # Search by code or license_plate
    equipment = db.query(Equipment).filter(
        Equipment.is_active == True,
        (Equipment.code == code) | (Equipment.license_plate == code) | (Equipment.qr_code == code)
    ).first()
    
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ציוד לא נמצא"
        )
    
    # Get supplier name
    result = {
        "id": equipment.id,
        "code": equipment.code,
        "name": equipment.name,
        "license_plate": equipment.license_plate,
        "equipment_type": equipment.equipment_type,
        "supplier_id": equipment.supplier_id,
        "hourly_rate": float(equipment.hourly_rate) if equipment.hourly_rate else None,
        "daily_rate": float(equipment.daily_rate) if equipment.daily_rate else None,
        "status": equipment.status,
        "is_active": equipment.is_active,
    }
    
    if equipment.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == equipment.supplier_id).first()
        if supplier:
            result["supplier_name"] = supplier.name
    
    return result


@router.post("/validate-plate")
def validate_license_plate(
    body: dict,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Validate equipment by license plate against an approved work order.
    """
    require_permission(current_user, "equipment.read")
    from app.models.equipment import Equipment
    from app.models.work_order import WorkOrder
    from app.models.supplier import Supplier
    from app.models.supplier_equipment import SupplierEquipment
    from app.core.enums import WorkOrderStatus

    plate = (body.get("license_plate") or "").strip()
    wo_id = body.get("work_order_id")
    if not plate:
        raise HTTPException(status_code=400, detail="חובה להזין מספר רישוי")

    eq = db.query(Equipment).filter(Equipment.is_active == True, Equipment.license_plate == plate).first()
    se = None
    if not eq:
        se = db.query(SupplierEquipment).filter(SupplierEquipment.license_plate == plate, SupplierEquipment.is_active == True).first()
    if not eq and not se:
        raise HTTPException(status_code=404, detail=f"לא נמצא כלי עם מספר רישוי: {plate}")

    supplier_id = (eq.supplier_id if eq else se.supplier_id) if (eq or se) else None
    equipment_name = (eq.name if eq else None) or "כלי"
    equipment_id = eq.id if eq else None
    result = {"valid": True, "license_plate": plate, "equipment_id": equipment_id,
              "supplier_equipment_id": se.id if se else None, "equipment_name": equipment_name,
              "supplier_id": supplier_id, "warnings": []}

    if wo_id:
        wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id, WorkOrder.deleted_at.is_(None)).first()
        if not wo:
            raise HTTPException(status_code=404, detail="הזמנת עבודה לא נמצאה")
        if wo.status not in (WorkOrderStatus.APPROVED_AND_SENT, "APPROVED_AND_SENT"):
            result["valid"] = False
            result["warnings"].append(f"הזמנה לא מאושרת (סטטוס: {wo.status})")
        if supplier_id and wo.supplier_id and supplier_id != wo.supplier_id:
            wo_supplier = db.query(Supplier).filter(Supplier.id == wo.supplier_id).first()
            result["valid"] = False
            result["warnings"].append(f"הכלי שייך לספק אחר. ספק מאושר: {wo_supplier.name if wo_supplier else wo.supplier_id}")
        result["work_order_id"] = wo.id
        result["work_order_status"] = wo.status
        if supplier_id:
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            result["supplier_name"] = supplier.name if supplier else None
    return result


@router.post("/{equipment_id}/scan")
def scan_equipment(
    equipment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    scan_type: str = "field_check",
    location: Optional[str] = None
):
    """
    Record an equipment scan
    
    Permissions: equipment.scan or equipment.read
    """
    from app.models.equipment import Equipment
    from datetime import datetime
    
    # Get equipment
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ציוד לא נמצא"
        )
    
    # Find active work order for this equipment
    from app.models.work_order import WorkOrder
    from sqlalchemy import text as sa_text
    
    active_wo = db.query(WorkOrder).filter(
        WorkOrder.equipment_id == equipment_id,
        WorkOrder.status.in_(["ACCEPTED", "IN_PROGRESS", "PENDING"]),
        WorkOrder.is_active == True,
    ).first()
    
    now = datetime.utcnow()
    db.execute(sa_text("""
        INSERT INTO equipment_scans
            (equipment_id, work_order_id, scanned_by, scan_type, scan_value, scan_timestamp, status, is_active, created_at, updated_at)
        VALUES
            (:eq_id, :wo_id, :user_id, :scan_type, :scan_value, :ts, 'completed', true, :now, :now)
    """), {
        "eq_id": equipment_id,
        "wo_id": active_wo.id if active_wo else None,
        "user_id": current_user.id,
        "scan_type": scan_type,
        "scan_value": str(equipment_id),
        "ts": now,
        "now": now,
    })
    
    # Update work order status to IN_PROGRESS if it was ACCEPTED
    if active_wo and active_wo.status == "ACCEPTED":
        active_wo.status = "IN_PROGRESS"
        active_wo.updated_at = now
    
    db.commit()
    
    # Log activity
    from app.services.activity_logger import log_equipment_scanned
    log_equipment_scanned(db=db, equipment_scan_id=0, user_id=current_user.id, equipment_id=equipment_id, scan_type=scan_type)
    
    return {
        "success": True,
        "message": "סריקה נרשמה בהצלחה",
        "equipment_id": equipment_id,
        "equipment_code": equipment.code,
        "scanned_by": current_user.id,
        "scan_type": scan_type,
        "scan_date": str(now.date()),
        "work_order_id": active_wo.id if active_wo else None,
        "scanned_at": now.isoformat()
    }


@router.post("/{equipment_id}/release")
def release_equipment(
    equipment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    work_order_id: Optional[int] = None,
    notes: Optional[str] = None
):
    """
    Release/Return equipment from work order.
    
    Business rules:
    1. Equipment status  AVAILABLE
    2. Work Order status  COMPLETED (if provided)
    3. Budget release triggered
    4. Activity log recorded
    
    This is NOT delete - history is preserved.
    """
    from app.models.equipment import Equipment
    from app.models.work_order import WorkOrder
    from datetime import datetime as dt
    from sqlalchemy import text as sa_text
    
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="ציוד לא נמצא")
    
    result = {
        "equipment_id": equipment_id,
        "previous_status": equipment.status,
        "actions_taken": [],
    }
    
    # 1. Release equipment  AVAILABLE
    old_status = equipment.status
    equipment.status = "available"
    equipment.updated_at = dt.utcnow()
    result["actions_taken"].append(f"equipment status: {old_status}  available")
    
    # 2. Complete work order if provided
    if work_order_id:
        wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if wo:
            old_wo_status = wo.status
            wo.status = "COMPLETED"
            wo.updated_at = dt.utcnow()
            result["work_order_id"] = work_order_id
            result["actions_taken"].append(f"work_order status: {old_wo_status}  COMPLETED")
    
    # 3. Budget release (mark frozen amount as released)
    # For now: log the event. Full budget logic depends on your budget model.
    result["actions_taken"].append("budget_release: logged (implement per budget rules)")
    
    db.commit()
    
    # 4. Activity log
    from app.services.activity_logger import _log
    _log(
        db=db,
        activity_type="equipment",
        action="equipment.released",
        user_id=current_user.id,
        entity_type="equipment",
        entity_id=equipment_id,
        details={
            "work_order_id": work_order_id,
            "notes": notes,
            "description_he": f"כלי #{equipment_id} שוחרר מהזמנה"
        }
    )
    
    result["success"] = True
    result["message"] = "הכלי שוחרר בהצלחה"
    result["new_status"] = "available"
    
    return result


# ============================================
# GENERIC ID ROUTE - MUST COME AFTER SPECIFIC ROUTES
# ============================================

@router.get("/{equipment_id}", response_model=EquipmentResponse)
def get_equipment(
    equipment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get equipment by ID
    
    Permissions: equipment.read
    """
    # Check permission
    require_permission(current_user, "equipment.read")
    
    try:
        equipment = equipment_service.get_by_id_or_404(db, equipment_id, include_deleted=False)
        return equipment
    
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.post("", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
def create_equipment(
    data: EquipmentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Create new equipment
    
    Permissions: equipment.create
    """
    # Check permission
    require_permission(current_user, "equipment.create")
    
    try:
        equipment = equipment_service.create(db, data, current_user_id=current_user.id)
        return equipment
    
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DuplicateException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.put("/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    equipment_id: int,
    data: EquipmentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Update equipment
    
    Permissions: equipment.update
    """
    # Check permission
    require_permission(current_user, "equipment.update")
    
    try:
        equipment = equipment_service.update(db, equipment_id, data, current_user_id=current_user.id)
        return equipment
    
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DuplicateException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(
    equipment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Delete equipment (soft delete)
    
    Permissions: equipment.delete
    """
    # Check permission
    require_permission(current_user, "equipment.delete")
    
    try:
        equipment_service.soft_delete(db, equipment_id, current_user_id=current_user.id)
        return None
    
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.patch("/{equipment_id}/toggle-active")
def toggle_equipment_active(
    equipment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """הפעל / השבת כלי ציוד"""
    require_permission(current_user, "EQUIPMENT.UPDATE")
    eq = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="ציוד לא נמצא")
    eq.is_active = not eq.is_active
    db.commit()
    return {"id": equipment_id, "is_active": eq.is_active}


@router.post("/{equipment_id}/restore", response_model=EquipmentResponse)
def restore_equipment(
    equipment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Restore soft-deleted equipment
    
    Permissions: equipment.restore
    """
    # Check permission
    require_permission(current_user, "equipment.restore")
    
    try:
        equipment = equipment_service.restore(db, equipment_id, current_user_id=current_user.id)
        return equipment
    
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


@router.post("/{equipment_id}/assign", response_model=EquipmentResponse)
def assign_equipment(
    equipment_id: int,
    request: EquipmentAssignRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Assign equipment to project
    
    Permissions: equipment.assign
    """
    # Check permission
    require_permission(current_user, "equipment.assign")
    
    try:
        # Validate that project_id is provided in request
        if not request.project_id:
            raise ValidationException("project_id is required")
        
        # Create assignment
        assignment = equipment_service.assign_to_project(
            db=db,
            equipment_id=equipment_id,
            project_id=request.project_id,
            current_user_id=current_user.id,
            start_date=request.start_date,
            end_date=request.end_date,
            notes=request.notes
        )
        
        # Return updated equipment
        equipment = equipment_service.get_by_id_or_404(db, equipment_id)
        return equipment
    
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )


# ============================================
# ADDITIONAL ENDPOINTS
# ============================================

@router.put("/{equipment_id}/maintenance", response_model=EquipmentResponse)
def update_equipment_maintenance(
    equipment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    last_maintenance_date: Optional[str] = None,
    next_maintenance_date: Optional[str] = None,
    notes: Optional[str] = None
):
    """
    Update equipment maintenance info
    
    Permissions: equipment.update
    """
    require_permission(current_user, "equipment.update")
    
    try:
        # Build update data
        update_data = EquipmentUpdate()
        if last_maintenance_date:
            update_data.last_maintenance_date = last_maintenance_date
        if next_maintenance_date:
            update_data.next_maintenance_date = next_maintenance_date
        if notes:
            update_data.notes = notes
        
        equipment = equipment_service.update(db, equipment_id, update_data, current_user.id)
        return equipment
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )
