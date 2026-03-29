# app/routers/sync.py
"""
Offline sync endpoints for Electron app
"""
from typing import List, Dict, Any, Union
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.worklog import Worklog
from app.models.work_order import WorkOrder
from app.models.equipment import Equipment
from app.models.project import Project

router = APIRouter(prefix="/sync", tags=["sync"])

class SyncOperation(BaseModel):
    """Single sync operation"""
    operation_type: str  # create_worklog, update_worklog, create_order, etc.
    entity_type: str     # worklog, work_order, equipment, etc.
    entity_id: Union[int, None]  # None for create operations
    data: Dict[str, Any]
    timestamp: datetime
    client_id: str  # Unique client identifier

class SyncBatchRequest(BaseModel):
    """Batch sync request"""
    operations: List[SyncOperation]
    client_id: str
    last_sync: datetime

class SyncResult(BaseModel):
    """Result of a sync operation"""
    operation_type: str
    entity_type: str
    entity_id: Union[int, None]
    success: bool
    error: Union[str, None] = None
    server_timestamp: datetime
    client_id: str

class SyncBatchResponse(BaseModel):
    """Batch sync response"""
    results: List[SyncResult]
    server_timestamp: datetime
    conflicts: List[Dict[str, Any]] = []

@router.post("/batch", response_model=SyncBatchResponse)
async def sync_batch(
    request: SyncBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Process batch sync operations"""
    try:
        results = []
        conflicts = []
        
        for operation in request.operations:
            try:
                result = await process_sync_operation(
                    operation, db, current_user
                )
                results.append(result)
                
            except Exception as e:
                # Handle conflicts and errors
                error_result = SyncResult(
                    operation_type=operation.operation_type,
                    entity_type=operation.entity_type,
                    entity_id=operation.entity_id,
                    success=False,
                    error=str(e),
                    server_timestamp=datetime.utcnow(),
                    client_id=operation.client_id
                )
                results.append(error_result)
                
                # Check if it's a conflict (entity modified since last sync)
                if "conflict" in str(e).lower():
                    conflicts.append({
                        "entity_type": operation.entity_type,
                        "entity_id": operation.entity_id,
                        "client_data": operation.data,
                        "server_data": await get_server_data(operation, db),
                        "conflict_reason": str(e)
                    })
        
        return SyncBatchResponse(
            results=results,
            server_timestamp=datetime.utcnow(),
            conflicts=conflicts
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )

async def process_sync_operation(
    operation: SyncOperation,
    db: Session,
    current_user: User
) -> SyncResult:
    """Process a single sync operation"""
    
    if operation.operation_type == "create_worklog":
        return await create_worklog(operation, db, current_user)
    
    elif operation.operation_type == "update_worklog":
        return await update_worklog(operation, db, current_user)
    
    elif operation.operation_type == "create_work_order":
        return await create_work_order(operation, db, current_user)
    
    elif operation.operation_type == "update_work_order":
        return await update_work_order(operation, db, current_user)
    
    elif operation.operation_type == "update_equipment":
        return await update_equipment(operation, db, current_user)
    
    else:
        raise ValueError(f"Unknown operation type: {operation.operation_type}")

async def create_worklog(
    operation: SyncOperation,
    db: Session,
    current_user: User
) -> SyncResult:
    """Create a new worklog — routed through WorklogService for full validation"""
    from app.services.worklog_service import WorklogService
    from app.schemas.worklog import WorklogCreate

    required_fields = ["work_order_id", "work_date", "hours_worked"]
    for field in required_fields:
        if field not in operation.data:
            raise ValueError(f"Missing required field: {field}")

    create_data = WorklogCreate(
        work_order_id=operation.data["work_order_id"],
        report_date=operation.data.get("work_date"),
        work_hours=operation.data.get("hours_worked"),
        report_type=operation.data.get("report_type", "standard"),
        break_hours=operation.data.get("break_hours", 0),
        equipment_scanned=operation.data.get("equipment_scanned"),
        activity_description=operation.data.get("description"),
        notes=operation.data.get("notes"),
    )

    service = WorklogService()
    worklog = service.create(db, create_data, current_user.id)

    return SyncResult(
        operation_type=operation.operation_type,
        entity_type=operation.entity_type,
        entity_id=worklog.id,
        success=True,
        server_timestamp=datetime.utcnow(),
        client_id=operation.client_id
    )

async def update_worklog(
    operation: SyncOperation,
    db: Session,
    current_user: User
) -> SyncResult:
    """Update an existing worklog — safe allowlist only"""
    from app.services.worklog_service import WorklogService
    from app.schemas.worklog import WorklogUpdate

    worklog = db.query(Worklog).filter(Worklog.id == operation.entity_id).first()
    if not worklog:
        raise ValueError(f"Worklog {operation.entity_id} not found")

    if worklog.updated_at and operation.timestamp < worklog.updated_at:
        raise ValueError(f"Conflict: Worklog {operation.entity_id} was modified after client sync")

    update_data = WorklogUpdate(
        work_hours=operation.data.get("work_hours") or operation.data.get("hours_worked"),
        break_hours=operation.data.get("break_hours"),
        activity_description=operation.data.get("description") or operation.data.get("activity_description"),
        notes=operation.data.get("notes"),
    )

    service = WorklogService()
    worklog = service.update(db, worklog.id, update_data, current_user.id)

    return SyncResult(
        operation_type=operation.operation_type,
        entity_type=operation.entity_type,
        entity_id=worklog.id,
        success=True,
        server_timestamp=datetime.utcnow(),
        client_id=operation.client_id
    )

async def create_work_order(
    operation: SyncOperation,
    db: Session,
    current_user: User
) -> SyncResult:
    """Create a new work order"""
    try:
        # Validate required fields
        required_fields = ["title", "project_id", "equipment_type"]
        for field in required_fields:
            if field not in operation.data:
                raise ValueError(f"Missing required field: {field}")
        
        # Create work order
        work_order = WorkOrder(
            title=operation.data["title"],
            project_id=operation.data["project_id"],
            equipment_type=operation.data["equipment_type"],
            description=operation.data.get("description", ""),
            supplier_id=operation.data.get("supplier_id"),
            work_start_date=operation.data.get("work_start_date"),
            work_end_date=operation.data.get("work_end_date"),
            estimated_hours=operation.data.get("estimated_hours"),
            hourly_rate=operation.data.get("hourly_rate"),
            created_by_id=current_user.id,
            created_at=datetime.utcnow()
        )
        
        db.add(work_order)
        db.commit()
        db.refresh(work_order)
        
        return SyncResult(
            operation_type=operation.operation_type,
            entity_type=operation.entity_type,
            entity_id=work_order.id,
            success=True,
            server_timestamp=datetime.utcnow(),
            client_id=operation.client_id
        )
        
    except Exception as e:
        db.rollback()
        raise e

async def update_work_order(
    operation: SyncOperation,
    db: Session,
    current_user: User
) -> SyncResult:
    """Update an existing work order"""
    try:
        work_order = db.query(WorkOrder).filter(WorkOrder.id == operation.entity_id).first()
        if not work_order:
            raise ValueError(f"Work order {operation.entity_id} not found")
        
        # Check for conflicts
        if work_order.updated_at and operation.timestamp < work_order.updated_at:
            raise ValueError(f"Conflict: Work order {operation.entity_id} was modified after client sync")
        
        # Update fields
        for field, value in operation.data.items():
            if hasattr(work_order, field):
                setattr(work_order, field, value)
        
        work_order.updated_at = datetime.utcnow()
        
        db.commit()
        
        return SyncResult(
            operation_type=operation.operation_type,
            entity_type=operation.entity_type,
            entity_id=work_order.id,
            success=True,
            server_timestamp=datetime.utcnow(),
            client_id=operation.client_id
        )
        
    except Exception as e:
        db.rollback()
        raise e

async def update_equipment(
    operation: SyncOperation,
    db: Session,
    current_user: User
) -> SyncResult:
    """Update equipment status/location"""
    try:
        equipment = db.query(Equipment).filter(Equipment.id == operation.entity_id).first()
        if not equipment:
            raise ValueError(f"Equipment {operation.entity_id} not found")
        
        # Check for conflicts
        if equipment.updated_at and operation.timestamp < equipment.updated_at:
            raise ValueError(f"Conflict: Equipment {operation.entity_id} was modified after client sync")
        
        # Update fields
        for field, value in operation.data.items():
            if hasattr(equipment, field):
                setattr(equipment, field, value)
        
        equipment.updated_at = datetime.utcnow()
        
        db.commit()
        
        return SyncResult(
            operation_type=operation.operation_type,
            entity_type=operation.entity_type,
            entity_id=equipment.id,
            success=True,
            server_timestamp=datetime.utcnow(),
            client_id=operation.client_id
        )
        
    except Exception as e:
        db.rollback()
        raise e

async def get_server_data(
    operation: SyncOperation,
    db: Session
) -> Dict[str, Any]:
    """Get current server data for conflict resolution"""
    if operation.entity_type == "worklog":
        entity = db.query(Worklog).filter(Worklog.id == operation.entity_id).first()
    elif operation.entity_type == "work_order":
        entity = db.query(WorkOrder).filter(WorkOrder.id == operation.entity_id).first()
    elif operation.entity_type == "equipment":
        entity = db.query(Equipment).filter(Equipment.id == operation.entity_id).first()
    else:
        return {}
    
    if entity:
        return {
            "id": entity.id,
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
            "data": {c.name: getattr(entity, c.name) for c in entity.__table__.columns}
        }
    
    return {}

@router.get("/status")
async def get_sync_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sync status and pending operations"""
    try:
        # Get recent activity counts
        recent_worklogs = db.query(Worklog).filter(
            Worklog.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).count()
        
        recent_work_orders = db.query(WorkOrder).filter(
            WorkOrder.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).count()
        
        return {
            "status": "active",
            "server_timestamp": datetime.utcnow().isoformat(),
            "recent_activity": {
                "worklogs_today": recent_worklogs,
                "work_orders_today": recent_work_orders
            },
            "sync_capabilities": [
                "create_worklog",
                "update_worklog",
                "create_work_order",
                "update_work_order",
                "update_equipment"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="שגיאת שרת"
        )

