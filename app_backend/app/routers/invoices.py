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
from app.services.notification_service import notify_invoice_created, notify_invoice_approved
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

    # ACCOUNTANT/ADMIN/REGION_MANAGER see all invoices; other roles filtered by area
    user_role = getattr(getattr(current_user, 'role', None), 'code', '')
    if current_user.area_id is not None and user_role not in ('ACCOUNTANT', 'ADMIN', 'REGION_MANAGER'):
        search.area_id = current_user.area_id

    invoices, total = invoice_service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return InvoiceList(items=invoices, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


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


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get invoice"""
    require_permission(current_user, "invoices.read")
    # ACCOUNTANT and ADMIN see all invoices regardless of area
    user_role = getattr(getattr(current_user, 'role', None), 'code', '')
    no_area_filter = current_user.area_id is None or user_role in ('ACCOUNTANT', 'ADMIN', 'REGION_MANAGER')
    if no_area_filter:
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
        notify_invoice_approved(db, updated)
        return updated
    except NotFoundException as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        db.rollback()
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


# ──────────────────────────────────────────────────────────────────────────────
# POST /invoices/from-worklogs
# יצירת חשבונית מרשימת דיווחי שעות מאושרים
# ──────────────────────────────────────────────────────────────────────────────
from pydantic import BaseModel as _BaseModel
from typing import List as _List
from decimal import Decimal as _Decimal


class CreateInvoiceFromWorklogsRequest(_BaseModel):
    worklog_ids: _List[int]
    supplier_id: int
    project_id: int


class CreateInvoiceFromWorklogsResponse(_BaseModel):
    invoice_id: int
    invoice_number: str
    total_amount: float
    worklog_count: int
    status: str


@router.post("/from-worklogs", response_model=CreateInvoiceFromWorklogsResponse)
def create_invoice_from_worklogs(
    body: CreateInvoiceFromWorklogsRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    יצירת חשבונית מרשימת דיווחי שעות מאושרים.

    לוגיקה:
    1. שליפת כל ה-worklogs לפי worklog_ids
    2. בדיקה שכולם status='approved'
    3. חישוב סכום כולל לפי cost_before_vat (אם קיים) או total_hours × hourly_rate_snapshot
    4. יצירת invoice + invoice_items
    5. עדכון worklogs → status='invoiced'
    """
    require_permission(current_user, "invoices.create")

    from app.models.worklog import Worklog
    from app.models.invoice import Invoice
    from sqlalchemy import text
    from datetime import date, datetime

    if not body.worklog_ids:
        raise HTTPException(status_code=400, detail="חובה לספק לפחות worklog_id אחד")

    # 1. שליפת worklogs
    worklogs = db.query(Worklog).filter(Worklog.id.in_(body.worklog_ids)).all()
    if len(worklogs) != len(body.worklog_ids):
        found_ids = {w.id for w in worklogs}
        missing = set(body.worklog_ids) - found_ids
        raise HTTPException(status_code=404, detail=f"Worklogs לא נמצאו: {sorted(missing)}")

    # 2. בדיקה שכולם מאושרים
    non_approved = [w.id for w in worklogs if w.status != 'APPROVED']
    if non_approved:
        raise HTTPException(
            status_code=400,
            detail=f"Worklogs {non_approved} אינם במצב 'APPROVED'. יש לאשר אותם קודם."
        )

    # 3. חישוב סכום כולל — כולל עלות שמירת לילה
    # Load overnight_guard_rate from work_hour_settings
    overnight_rate_row = db.execute(text("SELECT overnight_guard_rate FROM work_hour_settings LIMIT 1")).fetchone()
    overnight_guard_rate = _Decimal(str(overnight_rate_row[0])) if overnight_rate_row and overnight_rate_row[0] else _Decimal("0")

    # Fetch related work orders for guard info (one query)
    wo_ids = [w.work_order_id for w in worklogs if w.work_order_id]
    wo_guard_map: dict = {}
    if wo_ids:
        from app.models.work_order import WorkOrder
        wos = db.query(WorkOrder).filter(WorkOrder.id.in_(wo_ids)).all()
        for wo in wos:
            wo_guard_map[wo.id] = {
                "requires_guard": getattr(wo, "requires_guard", False),
                "guard_days": getattr(wo, "guard_days", 0),
            }

    total = _Decimal("0")
    for w in worklogs:
        # Base cost
        if w.cost_before_vat is not None:
            line_base = _Decimal(str(w.cost_before_vat))
        elif w.total_hours and w.hourly_rate_snapshot:
            line_base = _Decimal(str(w.total_hours)) * _Decimal(str(w.hourly_rate_snapshot))
        else:
            line_base = _Decimal("0")

        # Overnight cost
        guard_info = wo_guard_map.get(w.work_order_id, {})
        overnight_cost = _Decimal("0")
        if guard_info.get("requires_guard") and guard_info.get("guard_days", 0) > 0 and overnight_guard_rate > 0:
            overnight_cost = _Decimal(str(guard_info["guard_days"])) * overnight_guard_rate

        total += line_base + overnight_cost

    # 4. יצירת invoice חדש
    VAT_RATE = _Decimal("0.17")
    subtotal = total
    tax_amount = (subtotal * VAT_RATE).quantize(_Decimal("0.01"))
    total_with_vat = subtotal + tax_amount

    # Generate invoice number via service helper
    invoice_number = invoice_service._generate_invoice_number(db)
    today = date.today()
    from datetime import timedelta
    due = today + timedelta(days=30)

    invoice_data = InvoiceCreate(
        invoice_number=invoice_number,
        supplier_id=body.supplier_id,
        project_id=body.project_id,
        issue_date=today,
        due_date=due,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_with_vat,
        status="DRAFT",
        notes=f"חשבונית אוטומטית מ-{len(worklogs)} דיווחי שעות מאושרים",
        paid_amount=_Decimal("0"),
    )

    try:
        invoice = invoice_service.create(db, invoice_data, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"שגיאה ביצירת חשבונית: {str(e)}")

    # 5. יצירת invoice_items + עדכון worklog status
    from sqlalchemy import text as sa_text

    # Check if invoice_items table has worklog_id column
    col_exists = db.execute(sa_text("""
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name='invoice_items' AND column_name='worklog_id'
    """)).scalar()

    for idx, w in enumerate(worklogs):
        # Re-calculate per-worklog cost (same logic as above)
        if w.cost_before_vat is not None:
            line_base = _Decimal(str(w.cost_before_vat))
        elif w.total_hours and w.hourly_rate_snapshot:
            line_base = _Decimal(str(w.total_hours)) * _Decimal(str(w.hourly_rate_snapshot))
        else:
            line_base = _Decimal("0")

        guard_info = wo_guard_map.get(w.work_order_id, {})
        overnight_cost = _Decimal("0")
        if guard_info.get("requires_guard") and guard_info.get("guard_days", 0) > 0 and overnight_guard_rate > 0:
            overnight_cost = _Decimal(str(guard_info["guard_days"])) * overnight_guard_rate
        line_total = line_base + overnight_cost

        desc_parts = [f"דיווח שעות #{w.report_number} — {w.report_date}"]
        if overnight_cost > 0:
            desc_parts.append(f"שמירת לילה: {guard_info['guard_days']} לילות × ₪{overnight_guard_rate}")

        if col_exists:
            db.execute(sa_text("""
                INSERT INTO invoice_items
                  (invoice_id, worklog_id, description, quantity, unit_price, total_price, line_number, created_at, updated_at)
                VALUES (:invoice_id, :worklog_id, :desc, 1, :unit, :total, :line_num, NOW(), NOW())
            """), {
                "invoice_id": invoice.id,
                "worklog_id": w.id,
                "desc": " | ".join(desc_parts),
                "unit": float(line_total),
                "total": float(line_total),
                "line_num": idx + 1,
            })
        # Update worklog status
        w.status = 'invoiced'
        w.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(invoice)

    return CreateInvoiceFromWorklogsResponse(
        invoice_id=invoice.id,
        invoice_number=invoice.invoice_number,
        total_amount=float(invoice.total_amount),
        worklog_count=len(worklogs),
        status=invoice.status,
    )


# ──────────────────────────────────────────────────────────────────────────────
# GET /invoices/{invoice_id}/items
# פריטי חשבונית כולל שמות ספק/פרויקט
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/{invoice_id}/items")
def get_invoice_items(
    invoice_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Return invoice items enriched with supplier/project names."""
    require_permission(current_user, "invoices.view")

    # Check invoice exists
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.deleted_at.is_(None)).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="חשבונית לא נמצאה")

    from sqlalchemy import text as sa_text

    # Items
    items = db.execute(sa_text("""
        SELECT ii.id, ii.invoice_id, ii.worklog_id, ii.description,
               ii.quantity, ii.unit_price, ii.total_price,
               w.report_date, w.total_hours, w.hourly_rate_snapshot,
               w.work_order_id
        FROM invoice_items ii
        LEFT JOIN worklogs w ON w.id = ii.worklog_id
        WHERE ii.invoice_id = :inv_id AND (ii.is_active IS NULL OR ii.is_active = true)
        ORDER BY ii.id
    """), {"inv_id": invoice_id}).fetchall()

    # Supplier and project enrichment
    supplier_name = None
    if invoice.supplier_id:
        from app.models.supplier import Supplier as SupplierModel
        s = db.query(SupplierModel).filter(SupplierModel.id == invoice.supplier_id).first()
        supplier_name = s.name if s else None

    project_name = None
    project_code = None
    if invoice.project_id:
        from app.models.project import Project as ProjectModel
        p = db.query(ProjectModel).filter(ProjectModel.id == invoice.project_id).first()
        if p:
            project_name = p.name
            project_code = p.code

    return {
        "invoice": {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "supplier_id": invoice.supplier_id,
            "supplier_name": supplier_name,
            "project_id": invoice.project_id,
            "project_name": project_name,
            "project_code": project_code,
            "issue_date": invoice.issue_date.isoformat() if invoice.issue_date else None,
            "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
            "subtotal": float(invoice.subtotal),
            "tax_amount": float(invoice.tax_amount),
            "total_amount": float(invoice.total_amount),
            "paid_amount": float(invoice.paid_amount),
            "balance_due": float(invoice.total_amount - invoice.paid_amount),
            "status": invoice.status,
            "notes": invoice.notes,
            "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
        },
        "items": [
            {
                "id": row.id,
                "worklog_id": row.worklog_id,
                "description": row.description,
                "quantity": float(row.quantity) if row.quantity else 1,
                "unit_price": float(row.unit_price) if row.unit_price else 0,
                "total_price": float(row.total_price) if row.total_price else 0,
                "report_date": row.report_date.isoformat() if row.report_date else None,
                "total_hours": float(row.total_hours) if row.total_hours else None,
                "hourly_rate": float(row.hourly_rate_snapshot) if row.hourly_rate_snapshot else None,
            }
            for row in items
        ],
    }


# ──────────────────────────────────────────────────────────────────────────────
# POST /invoices/{invoice_id}/mark-paid
# סמן חשבונית כשולמה
# ──────────────────────────────────────────────────────────────────────────────
@router.post("/{invoice_id}/mark-paid")
def mark_invoice_paid(
    invoice_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Mark invoice as paid."""
    require_permission(current_user, "invoices.approve")
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.deleted_at.is_(None)).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="חשבונית לא נמצאה")
    invoice.paid_amount = invoice.total_amount
    invoice.status = "PAID"
    from datetime import datetime
    invoice.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "החשבונית סומנה כשולמה", "invoice_id": invoice_id, "status": "PAID"}


# ── Monthly Invoice Generation ────────────────────────────────────────────────
from pydantic import BaseModel as _BaseModel


class MonthlyInvoiceRequest(_BaseModel):
    supplier_id: int
    project_id: int
    month: int
    year: int


@router.post("/generate-monthly", status_code=201)
def generate_monthly_invoice_endpoint(
    body: MonthlyInvoiceRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    מנהלת חשבונות מפיקה חשבונית חודשית לספק+פרויקט.
    מרכזת כל worklogs APPROVED של אותו חודש.
    """
    require_permission(current_user, "invoices.create")
    from app.services.invoice_service import generate_monthly_invoice
    try:
        invoice = generate_monthly_invoice(
            supplier_id=body.supplier_id,
            project_id=body.project_id,
            month=body.month,
            year=body.year,
            created_by=current_user.id,
            db=db,
        )
        notify_invoice_created(db, invoice)
        return {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "total_amount": float(invoice.total_amount),
            "status": invoice.status,
            "message": f"חשבונית {invoice.invoice_number} נוצרה בהצלחה",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/uninvoiced-suppliers")
def get_uninvoiced_suppliers_endpoint(
    project_id: int,
    month: int,
    year: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """ספקים עם דיווחים מאושרים שלא שויכו לחשבונית"""
    require_permission(current_user, "invoices.view")
    from app.services.invoice_service import get_uninvoiced_suppliers
    return get_uninvoiced_suppliers(project_id, month, year, db)
