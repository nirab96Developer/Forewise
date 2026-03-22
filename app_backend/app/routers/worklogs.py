"""
Worklogs Router
"""

from datetime import date
from typing import Annotated, Optional
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db

logger = logging.getLogger(__name__)
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.models.worklog import Worklog
from app.models.project import Project
from app.services.notification_service import (
    notify_worklog_created,
    notify_worklog_approved,
    notify_worklog_rejected,
)
from app.schemas.worklog import (
    WorklogCreate, WorklogUpdate, WorklogResponse,
    WorklogList, WorklogSearch, WorklogStatistics
)
from app.services.worklog_service import WorklogService
from app.core.exceptions import NotFoundException, ValidationException

router = APIRouter(prefix="/worklogs", tags=["Worklogs"])
worklog_service = WorklogService()


@router.get("", response_model=WorklogList)
def list_worklogs(
    search: Annotated[WorklogSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List worklogs"""
    require_permission(current_user, "worklogs.read")

    if current_user.area_id is not None:
        search.area_id = current_user.area_id

    worklogs, total = worklog_service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1

    return WorklogList(items=worklogs, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


# ============================================
# SPECIFIC ROUTES MUST COME BEFORE /{worklog_id}
# ============================================

@router.get("/my-worklogs", response_model=WorklogList)
def get_my_worklogs_endpoint(
    search: Annotated[WorklogSearch, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get worklogs created by the current user.
    This route MUST be before /{worklog_id} to avoid matching "my-worklogs" as an ID.

    Permissions: worklogs.read_own (or worklogs.read)
    """
    # User can always read their own worklogs
    search.user_id = current_user.id
    worklogs, total = worklog_service.list(db, search)
    total_pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    return WorklogList(items=worklogs, total=total, page=search.page, page_size=search.page_size, total_pages=total_pages)


@router.get("/pending-approval", response_model=WorklogList)
def get_pending_approval_endpoint(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Get worklogs pending approval.
    This route MUST be before /{worklog_id} to avoid matching "pending-approval" as an ID.

    Permissions: worklogs.approve
    """
    require_permission(current_user, "worklogs.approve")
    search = WorklogSearch(status="SUBMITTED", page=page, page_size=page_size)
    worklogs, total = worklog_service.list(db, search)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return WorklogList(items=worklogs, total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.get("/statistics", response_model=WorklogStatistics)
def get_statistics_endpoint(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_id: Optional[int] = None,
    user_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
):
    """
    Get worklog statistics.
    This route MUST be before /{worklog_id} to avoid matching "statistics" as an ID.
    """
    require_permission(current_user, "worklogs.read")
    filters = {}
    if project_id: filters["project_id"] = project_id
    if user_id: filters["user_id"] = user_id
    if date_from: filters["date_from"] = str(date_from)
    if date_to: filters["date_to"] = str(date_to)
    stats = worklog_service.get_statistics(db, filters=filters if filters else None)
    return stats


@router.get("/activity-codes")
def get_activity_codes_endpoint(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get list of activity codes for worklog creation.
    This route MUST be before /{worklog_id} to avoid matching "activity-codes" as an ID.
    """
    from app.models.activity_type import ActivityType
    codes = db.query(ActivityType).filter(ActivityType.is_active == True).all()
    return [{"id": c.id, "code": c.code if hasattr(c, 'code') else str(c.id), "name": c.name if hasattr(c, 'name') else str(c.id)} for c in codes]


# ============================================
# GENERIC ID-BASED ROUTE - MUST BE AFTER SPECIFIC ROUTES
# ============================================

@router.get("/{worklog_id}", response_model=WorklogResponse)
def get_worklog(
    worklog_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get worklog"""
    require_permission(current_user, "worklogs.read")

    query = (
        select(Worklog)
        .join(Project, Project.id == Worklog.project_id)
        .where(Worklog.id == worklog_id)
    )

    if current_user.area_id is not None:
        query = query.where(Project.area_id == current_user.area_id)

    worklog = db.execute(query).scalar_one_or_none()
    if not worklog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worklog not found")
    return worklog


@router.post("", response_model=WorklogResponse, status_code=status.HTTP_201_CREATED)
def create_worklog(
    data: WorklogCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create worklog"""
    require_permission(current_user, "worklogs.create")

    try:
        worklog = worklog_service.create(db, data, current_user.id)
        notify_worklog_created(db, worklog)
        
        # Send Stage 1 emails (best-effort)
        try:
            _send_worklog_stage1_emails(db, worklog, current_user)
        except Exception as e:
            logger.warning(f"Stage 1 email failed: {e}")
        
        return worklog
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/standard", response_model=WorklogResponse, status_code=status.HTTP_201_CREATED)
def create_standard_worklog(
    work_order_id: int,
    report_date: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create standard worklog - 9 net work hours (+ 1.5 break, not counted)
    תקן: 9 שעות עבודה נטו. הפסקה 1.5 שעות לא נספרת.
    """
    require_permission(current_user, "worklogs.create")

    try:
        from datetime import date as date_type
        from decimal import Decimal

        # Parse date
        parsed_date = date_type.fromisoformat(report_date)

        # Create standard worklog data — total_hours = net work hours only (×9)
        data = WorklogCreate(
            work_order_id=work_order_id,
            report_date=parsed_date,
            report_type="standard",
            work_hours=Decimal("9.0"),
            break_hours=Decimal("1.5"),
            total_hours=Decimal("9"),
            is_standard=True,
            notes=notes
        )

        worklog = worklog_service.create(db, data, current_user.id)
        return worklog
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/manual", response_model=WorklogResponse, status_code=status.HTTP_201_CREATED)
def create_manual_worklog(
    work_order_id: int,
    report_date: str,
    activity_code: str,
    work_hours: float,
    break_hours: float = 0,
    activity_description: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create manual worklog with activity code (1-14)
    דיווח ידני עם קוד פעילות
    """
    require_permission(current_user, "worklogs.create")

    try:
        from datetime import date as date_type
        from decimal import Decimal

        # Parse date
        parsed_date = date_type.fromisoformat(report_date)

        # Calculate total hours
        total = Decimal(str(work_hours)) + Decimal(str(break_hours))

        # Create manual worklog data
        data = WorklogCreate(
            work_order_id=work_order_id,
            report_date=parsed_date,
            report_type="manual",
            work_hours=Decimal(str(work_hours)),
            break_hours=Decimal(str(break_hours)),
            total_hours=total,
            is_standard=False,
            work_type=activity_code,
            activity_description=activity_description,
            notes=notes
        )

        worklog = worklog_service.create(db, data, current_user.id)
        return worklog
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/storage", response_model=WorklogResponse, status_code=status.HTTP_201_CREATED)
def create_storage_worklog(
    work_order_id: int,
    report_date: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create storage worklog - equipment storage overnight (150 NIS per night)
    דיווח אחסון כלים - 150 ש"ח ללילה
    """
    require_permission(current_user, "worklogs.create")

    try:
        from datetime import date as date_type
        from decimal import Decimal

        # Parse date
        parsed_date = date_type.fromisoformat(report_date)

        # Create storage worklog - fixed rate 150 NIS
        data = WorklogCreate(
            work_order_id=work_order_id,
            report_date=parsed_date,
            report_type="storage",
            work_hours=Decimal("0"),  # No work hours for storage
            break_hours=Decimal("0"),
            total_hours=Decimal("0"),
            is_standard=False,
            work_type="storage",
            activity_description="אחסון כלים - 150 ש״ח ללילה",
            notes=notes
        )

        worklog = worklog_service.create(db, data, current_user.id)
        return worklog
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{worklog_id}", response_model=WorklogResponse)
def update_worklog(
    worklog_id: int,
    data: WorklogUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update worklog"""
    require_permission(current_user, "worklogs.update")

    try:
        worklog = worklog_service.update(db, worklog_id, data, current_user.id)
        return worklog
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{worklog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worklog(
    worklog_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Deactivate worklog (TRANSACTIONS - uses is_active)"""
    require_permission(current_user, "worklogs.delete")

    try:
        worklog_service.deactivate(db, worklog_id, current_user.id)
        return None
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{worklog_id}/activate", response_model=WorklogResponse)
def activate_worklog(
    worklog_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Activate worklog"""
    require_permission(current_user, "worklogs.restore")

    try:
        worklog = worklog_service.activate(db, worklog_id, current_user.id)
        return worklog
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/by-work-order/{work_order_id}", response_model=WorklogList)
def get_worklogs_by_work_order(
    work_order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get worklogs for specific work order"""
    require_permission(current_user, "worklogs.read")

    search = WorklogSearch(work_order_id=work_order_id, page=1, page_size=100)
    worklogs, total = worklog_service.list(db, search)

    return WorklogList(items=worklogs, total=total, page=1, page_size=100, total_pages=1)


# ============================================
# WORKFLOW ACTION ENDPOINTS
# ============================================

@router.post("/{worklog_id}/submit", response_model=WorklogResponse)
def submit_worklog(
    worklog_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    notes: Optional[str] = None
):
    """
    Submit worklog for approval

    Permissions: worklogs.submit (or owner)
    """
    try:
        # Check if owner or has permission
        worklog = worklog_service.get_by_id(db, worklog_id)
        if not worklog:
            raise HTTPException(status_code=404, detail="דיווח לא נמצא")
        if worklog.user_id != current_user.id:
            require_permission(current_user, "worklogs.submit")

        # ============================================
        # SCAN GATE: חובה סריקה יומית לפני הגשת דיווח
        # Enterprise validation rules:
        #   1. WO must have equipment_id
        #   2. WO must be in valid status (not CANCELLED/COMPLETED/DRAFT)
        #   3. Scan must exist for same equipment + same report_date
        #   4. One scan per day is enough for all worklogs that day
        # ============================================
        if worklog.work_order_id:
            from app.models.work_order import WorkOrder
            from sqlalchemy import text as sa_text
            
            wo = db.query(WorkOrder).filter(WorkOrder.id == worklog.work_order_id).first()
            
            if wo:
                # Rule: WO must be in valid status for reporting
                # COMPLETED = נעול לדיווחים חדשים (הזמנה שנסגרה)
                blocked_statuses = ["CANCELLED", "EXPIRED", "DRAFT", "COMPLETED"]
                if wo.status in blocked_statuses:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "message": f"לא ניתן לדווח על הזמנה בסטטוס {wo.status}",
                            "error_code": "WO_STATUS_INVALID",
                            "work_order_id": wo.id,
                            "status": wo.status,
                        }
                    )
                
                # Rule: Scan required only when WO is ACCEPTED or IN_PROGRESS
                scan_required_statuses = ["ACCEPTED", "IN_PROGRESS"]
                if wo.equipment_id and wo.status in scan_required_statuses:
                    report_date = worklog.report_date
                    if report_date:
                        # Check scan for SAME equipment + SAME day
                        scan_exists = db.execute(sa_text("""
                            SELECT COUNT(*) FROM equipment_scans 
                            WHERE equipment_id = :eq_id 
                            AND scan_date = :scan_date 
                            AND is_valid = true
                        """), {"eq_id": wo.equipment_id, "scan_date": report_date}).scalar()
                        
                        if not scan_exists or scan_exists == 0:
                            raise HTTPException(
                                status_code=422,
                                detail={
                                    "message": "חובה סריקת כלי לפני הגשת דיווח",
                                    "error_code": "SCAN_REQUIRED",
                                    "equipment_id": wo.equipment_id,
                                    "work_order_id": wo.id,
                                    "report_date": str(report_date),
                                    "scan_url": f"/equipment/{wo.equipment_id}/scan",
                                    "help": "יש לבצע סריקה של הכלי ביום העבודה לפני שליחת הדיווח"
                                }
                            )
                        
                        # Mark worklog as scanned
                        worklog.equipment_scanned = True
                        worklog.scan_time = db.execute(sa_text("""
                            SELECT created_at FROM equipment_scans 
                            WHERE equipment_id = :eq_id AND scan_date = :scan_date AND is_valid = true
                            ORDER BY created_at DESC LIMIT 1
                        """), {"eq_id": wo.equipment_id, "scan_date": report_date}).scalar()

        # Use service method (handles log internally)
        updated = worklog_service.submit(db, worklog_id, current_user.id)
        return updated
    except HTTPException:
        raise
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit worklog: {str(e)}"
        )


@router.post("/{worklog_id}/approve", response_model=WorklogResponse)
def approve_worklog(
    worklog_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    background_tasks: BackgroundTasks = None,
    notes: Optional[str] = None
):
    """
    Approve worklog and send PDF report
    
    On approval, PDF is sent to:
    - Supplier (for their records)
    - Area Accountant (for billing)
    - Area Manager (for oversight)

    Permissions: worklogs.approve
    """
    require_permission(current_user, "worklogs.approve")

    try:
        # Use service method (handles log internally)
        updated = worklog_service.approve(db, worklog_id, current_user.id)
        notify_worklog_approved(db, updated)

        # Send PDF in background
        if background_tasks:
            background_tasks.add_task(
                send_approval_pdf,
                db, updated, current_user
            )
        
        return updated
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve worklog: {str(e)}"
        )


def send_approval_pdf(db: Session, worklog, current_user):
    """
    Background task to send approval PDF to all relevant parties
    """
    try:
        from app.services.pdf_service import generate_worklog_pdf
        from app.core.email import send_email_with_pdf
        from app.models.project import Project
        from app.models.supplier import Supplier
        from app.models.work_order import WorkOrder
        
        # Build worklog data for PDF
        worklog_data = {
            'id': worklog.id,
            'report_number': worklog.report_number,
            'work_date': worklog.report_date.strftime('%d/%m/%Y') if worklog.report_date else '',
            'project_name': '',
            'region_name': '',
            'area_name': '',
            'supplier_name': '',
            'supplier_phone': '',
            'equipment_code': '',
            'equipment_type': worklog.equipment_type or '',
            'total_hours': float(worklog.total_hours) if worklog.total_hours else 0,
            'billable_hours': float(worklog.paid_hours or worklog.net_hours or worklog.total_hours or 0),
            'idle_hours': 0,
            'start_time': worklog.start_time.strftime('%H:%M') if worklog.start_time else '',
            'end_time': worklog.end_time.strftime('%H:%M') if worklog.end_time else '',
            'notes': worklog.notes or '',
            'user_name': current_user.full_name or current_user.username if current_user else '',
            'approved_at': worklog.approved_at.strftime('%d/%m/%Y %H:%M') if worklog.approved_at else '',
            'is_standard': worklog.is_standard,
            'work_order_id': worklog.work_order_id,
        }
        
        # Load related data
        if worklog.project_id:
            project = db.query(Project).filter(Project.id == worklog.project_id).first()
            if project:
                worklog_data['project_name'] = project.name
                if project.region:
                    worklog_data['region_name'] = project.region.name
                if project.area:
                    worklog_data['area_name'] = project.area.name
        
        if worklog.work_order_id:
            work_order = db.query(WorkOrder).filter(WorkOrder.id == worklog.work_order_id).first()
            if work_order and work_order.supplier_id:
                supplier = db.query(Supplier).filter(Supplier.id == work_order.supplier_id).first()
                if supplier:
                    worklog_data['supplier_name'] = supplier.name
                    worklog_data['supplier_phone'] = supplier.phone or ''
        
        # Generate PDF
        pdf_bytes = generate_worklog_pdf(worklog_data)
        pdf_filename = f"worklog_{worklog.report_number}_{worklog.report_date.strftime('%Y%m%d') if worklog.report_date else 'report'}.pdf"
        
        # Send to supplier (if email available)
        if worklog_data.get('supplier_email'):
            try:
                send_email_with_pdf(
                    to=worklog_data['supplier_email'],
                    subject=f"אישור דיווח עבודה מס' {worklog.report_number} - Forewise",
                    body=f"""שלום רב,

מצורף אישור דיווח עבודה יומי מספר {worklog.report_number}.

פרטי הדיווח:
• פרויקט: {worklog_data['project_name']}
• תאריך: {worklog_data['work_date']}
• שעות לתשלום: {worklog_data.get('billable_hours', 0)}

בברכה,
מערכת ניהול יערות Forewise""",
                    pdf_bytes=pdf_bytes,
                    pdf_filename=pdf_filename
                )
            except Exception as e:
                logger.error(f"Failed to send PDF to supplier: {e}")
        
        # Log success
        logger.info(f"Approval PDF generated for worklog {worklog.id}")
        
    except Exception as e:
        logger.error(f"Error sending approval PDF: {e}")


@router.post("/{worklog_id}/reject", response_model=WorklogResponse)
def reject_worklog(
    worklog_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    rejection_reason: Optional[str] = None
):
    """
    Reject worklog

    Permissions: worklogs.approve
    """
    require_permission(current_user, "worklogs.approve")

    try:
        # Use service method (handles log internally)
        updated = worklog_service.reject(db, worklog_id, current_user.id, rejection_reason)
        notify_worklog_rejected(db, updated, reason=rejection_reason or "")
        return updated
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject worklog: {str(e)}"
        )


def _send_worklog_stage1_emails(db, worklog, current_user):
    """Send Stage 1 emails: accountant + supplier + worker."""
    from app.core.email import send_email
    from app.templates.email_worklog import stage1_pending
    from app.services.worklog_service import WorklogService
    from sqlalchemy import text

    report_number = WorklogService.format_report_number(worklog.report_number or worklog.id)
    project_name = ""
    supplier_name = ""
    supplier_email = ""
    equipment_type = getattr(worklog, 'equipment_type', '') or ''
    license_plate = ""
    hourly_rate = float(getattr(worklog, 'hourly_rate_snapshot', 0) or 0)

    if worklog.project_id:
        row = db.execute(text("SELECT name FROM projects WHERE id=:pid"), {"pid": worklog.project_id}).first()
        if row: project_name = row[0]

    if getattr(worklog, 'work_order_id', None):
        row = db.execute(text(
            "SELECT s.name, s.email FROM work_orders wo JOIN suppliers s ON wo.supplier_id=s.id WHERE wo.id=:wid"
        ), {"wid": worklog.work_order_id}).first()
        if row: supplier_name, supplier_email = row[0] or "", row[1] or ""

    if getattr(worklog, 'equipment_id', None):
        row = db.execute(text("SELECT license_plate, equipment_type FROM equipment WHERE id=:eid"), {"eid": worklog.equipment_id}).first()
        if row:
            license_plate = row[0] or ""
            if not equipment_type: equipment_type = row[1] or ""

    work_date = str(getattr(worklog, 'report_date', '') or '')
    work_hours = float(getattr(worklog, 'work_hours', 0) or getattr(worklog, 'total_hours', 0) or 0)
    report_type = getattr(worklog, 'report_type', 'standard') or 'standard'
    worker_name = current_user.full_name or current_user.username or ''
    overnight = int(getattr(worklog, 'overnight_nights', 0) or 0)

    common = dict(
        report_number=report_number, project_name=project_name,
        supplier_name=supplier_name, equipment_type=equipment_type,
        license_plate=license_plate, work_date=work_date,
        work_hours=work_hours, report_type=report_type,
        worker_name=worker_name, hourly_rate=hourly_rate,
        overnight_nights=overnight,
    )

    # 1. Accountant
    acct_rows = db.execute(text("""
        SELECT u.email FROM users u JOIN roles r ON u.role_id=r.id
        WHERE r.code='ACCOUNTANT' AND u.is_active=true AND u.email IS NOT NULL
    """)).fetchall()
    for row in acct_rows:
        tmpl = stage1_pending(**common, recipient_role="accountant")
        send_email(to=row[0], subject=tmpl["subject"], body="", html_body=tmpl["html"])

    # 2. Supplier
    if supplier_email:
        tmpl = stage1_pending(**common, recipient_role="supplier")
        send_email(to=supplier_email, subject=tmpl["subject"], body="", html_body=tmpl["html"])

    # 3. Worker
    if current_user.email:
        tmpl = stage1_pending(**common, recipient_role="worker")
        send_email(to=current_user.email, subject=tmpl["subject"], body="", html_body=tmpl["html"])
