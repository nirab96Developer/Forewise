"""
Invoices Router
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.models.invoice import Invoice
from app.models.project import Project
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    InvoiceList, InvoiceSearch, InvoiceStatistics
)
from app.services.invoice_service import InvoiceService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException

router = APIRouter(prefix="/invoices", tags=["Invoices"])
invoice_service = InvoiceService()


@router.get("", response_model=InvoiceList)
def list_invoices(
    search: Annotated[InvoiceSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List invoices"""
    require_permission(current_user, "invoices.read")

    if current_user.area_id is not None:
        search.area_id = current_user.area_id

    invoices, total = invoice_service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return InvoiceList(items=invoices, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get invoice"""
    require_permission(current_user, "invoices.read")
    if current_user.area_id is None:
        invoice = invoice_service.get_by_id_or_404(db, invoice_id)
        return invoice

    invoice = db.execute(
        select(Invoice)
        .join(Project, Project.id == Invoice.project_id)
        .where(
            Invoice.id == invoice_id,
            Project.area_id == current_user.area_id,
        )
    ).scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    data: InvoiceCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create invoice"""
    require_permission(current_user, "invoices.create")
    try:
        invoice = invoice_service.create(db, data, current_user.id)
        return invoice
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update invoice"""
    require_permission(current_user, "invoices.update")
    try:
        invoice = invoice_service.update(db, invoice_id, data, current_user.id)
        return invoice
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationException, DuplicateException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Delete invoice"""
    require_permission(current_user, "invoices.delete")
    try:
        invoice_service.soft_delete(db, invoice_id, current_user.id)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{invoice_id}/restore", response_model=InvoiceResponse)
def restore_invoice(
    invoice_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Restore invoice"""
    require_permission(current_user, "invoices.restore")
    invoice = invoice_service.restore(db, invoice_id, current_user.id)
    return invoice


@router.get("/statistics", response_model=InvoiceStatistics)
def get_statistics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    supplier_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None)
):
    """Get statistics"""
    require_permission(current_user, "invoices.read")
    filters = {}
    if supplier_id:
        filters['supplier_id'] = supplier_id
    if project_id:
        filters['project_id'] = project_id
    return invoice_service.get_statistics(db, filters)


@router.get("/by-number/{invoice_number}", response_model=InvoiceResponse)
def get_by_number(
    invoice_number: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get by invoice number"""
    require_permission(current_user, "invoices.read")
    invoice = invoice_service.get_by_number(db, invoice_number)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invoice '{invoice_number}' not found")
    return invoice


# ============================================
# FRONTEND COMPATIBILITY ENDPOINTS
# ============================================

@router.get("/summary/stats", response_model=InvoiceStatistics)
def get_summary_stats(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_id: Optional[int] = Query(None)
):
    """
    Get invoice summary statistics - alias for /statistics
    """
    require_permission(current_user, "invoices.read")
    filters = {}
    if project_id:
        filters['project_id'] = project_id
    return invoice_service.get_statistics(db, filters)


@router.post("/{invoice_id}/approve", response_model=InvoiceResponse)
def approve_invoice(
    invoice_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    notes: Optional[str] = None,
    send_to_supplier: bool = False
):
    """
    Approve invoice
    
    Permissions: invoices.approve
    """
    require_permission(current_user, "invoices.approve")
    
    try:
        # Use service method (handles log internally)
        updated = invoice_service.approve(db, invoice_id, current_user.id)
        return updated
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve invoice: {str(e)}"
        )


@router.post("/{invoice_id}/send")
def send_invoice_to_supplier(
    invoice_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Mark invoice as sent to supplier
    
    Permissions: invoices.update
    """
    require_permission(current_user, "invoices.update")
    
    try:
        # Use service method (handles log internally)
        invoice_service.send_to_supplier(db, invoice_id, current_user.id)
        return {"message": "Invoice sent to supplier", "invoice_id": invoice_id}
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send invoice: {str(e)}"
        )


@router.post("/from-work-order/{work_order_id}", response_model=InvoiceResponse)
def create_invoice_from_work_order(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Create invoice from work order
    
    Permissions: invoices.create
    """
    require_permission(current_user, "invoices.create")
    
    try:
        # Get work order details
        from app.services.work_order_service import WorkOrderService
        wo_service = WorkOrderService()
        work_order = wo_service.get_by_id_or_404(db, work_order_id, include_deleted=False)
        
        # Create invoice from work order data
        invoice_data = InvoiceCreate(
            work_order_id=work_order_id,
            supplier_id=work_order.supplier_id,
            project_id=work_order.project_id,
            total_amount=0  # To be calculated
        )
        
        # Create invoice (log is handled in service)
        invoice = invoice_service.create(db, invoice_data, current_user.id)
        return invoice
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice from work order: {str(e)}"
        )
