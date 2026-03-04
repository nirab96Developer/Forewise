"""
Invoice Service
"""

from typing import Optional, List, Tuple
from decimal import Decimal
from datetime import date as dt_date
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.models.invoice import Invoice
from app.models.supplier import Supplier
from app.models.project import Project
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceSearch, InvoiceStatistics
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException


class InvoiceService(BaseService[Invoice]):
    """Invoice Service - CORE"""
    
    def __init__(self):
        super().__init__(Invoice)
    
    def _generate_invoice_number(self, db: Session) -> str:
        """Generate unique invoice number — finds lowest unused YYYY#### number."""
        import datetime as _dt
        year = _dt.datetime.now().year
        
        # Find highest numeric invoice_number for this year
        from sqlalchemy import text as _text
        max_num_row = db.execute(_text(
            "SELECT MAX(invoice_number::bigint) FROM invoices "
            "WHERE invoice_number ~ '^[0-9]+$' AND deleted_at IS NULL"
        )).scalar()

        if max_num_row:
            next_num = int(max_num_row) + 1
        else:
            next_num = int(f"{year}0001")

        # Ensure no collision (safety loop)
        while db.query(Invoice).filter(
            Invoice.invoice_number == str(next_num),
            Invoice.deleted_at.is_(None)
        ).first():
            next_num += 1

        return str(next_num)
    
    def create(self, db: Session, data: InvoiceCreate, current_user_id: int) -> Invoice:
        """Create invoice"""
        # UNIQUE: invoice_number
        existing = db.query(Invoice).filter(
            Invoice.invoice_number == data.invoice_number,
            Invoice.deleted_at.is_(None)
        ).first()
        if existing:
            raise DuplicateException(f"Invoice {data.invoice_number} already exists")
        
        # Validate FK: supplier_id (no FK in DB but validate anyway)
        supplier = db.query(Supplier).filter_by(id=data.supplier_id).first()
        if not supplier:
            raise ValidationException(f"Supplier {data.supplier_id} not found")
        if not supplier.is_active:
            raise ValidationException(f"Supplier {data.supplier_id} is not active")
        
        # Validate FK: project_id (if provided)
        if data.project_id:
            project = db.query(Project).filter_by(id=data.project_id).first()
            if not project:
                raise ValidationException(f"Project {data.project_id} not found")
        
        # Create
        invoice_dict = data.model_dump(exclude_unset=True)
        invoice_dict['created_by'] = current_user_id
        invoice_dict['paid_amount'] = Decimal(0)
        
        invoice = Invoice(**invoice_dict)
        
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        # Notify accountants about new invoice
        project_name = ""
        if invoice.project_id:
            try:
                from app.models.project import Project as _Proj
                p = db.query(_Proj).filter(_Proj.id == invoice.project_id).first()
                if p: project_name = p.name or ""
            except Exception:
                pass
        _notify_accountants_invoice(db, invoice.id, invoice.invoice_number or str(invoice.id), project_name)

        return invoice
    
    def update(self, db: Session, invoice_id: int, data: InvoiceUpdate, current_user_id: int) -> Invoice:
        """Update invoice"""
        invoice = self.get_by_id_or_404(db, invoice_id)
        
        # Version check
        if data.version is not None and invoice.version != data.version:
            raise DuplicateException("Invoice was modified by another user")
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        # UNIQUE: invoice_number (if changed)
        if 'invoice_number' in update_dict and update_dict['invoice_number'] != invoice.invoice_number:
            existing = db.query(Invoice).filter(
                Invoice.invoice_number == update_dict['invoice_number'],
                Invoice.id != invoice_id,
                Invoice.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(f"Invoice {update_dict['invoice_number']} already exists")
        
        # Update
        for field, value in update_dict.items():
            setattr(invoice, field, value)
        
        if invoice.version is not None:
            invoice.version += 1
        
        db.commit()
        db.refresh(invoice)
        
        return invoice
    
    def list(self, db: Session, search: InvoiceSearch) -> Tuple[List[Invoice], int]:
        """List invoices"""
        query = self._base_query(db, include_deleted=search.include_deleted)
        
        if search.q:
            query = query.where(Invoice.invoice_number.ilike(f"%{search.q}%"))
        
        if search.supplier_id:
            query = query.where(Invoice.supplier_id == search.supplier_id)
        if search.project_id:
            query = query.where(Invoice.project_id == search.project_id)
        if search.status:
            query = query.where(Invoice.status == search.status.value)
        if search.issue_date_from:
            query = query.where(Invoice.issue_date >= search.issue_date_from)
        if search.issue_date_to:
            query = query.where(Invoice.issue_date <= search.issue_date_to)
        if search.is_active is not None:
            query = query.where(Invoice.is_active == search.is_active)
        
        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
        
        sort_col = getattr(Invoice, search.sort_by, Invoice.issue_date)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        offset = (search.page - 1) * search.page_size
        invoices = db.execute(query.offset(offset).limit(search.page_size)).scalars().all()
        
        return invoices, total
    
    def get_by_number(self, db: Session, invoice_number: str) -> Optional[Invoice]:
        """Get by invoice number"""
        return db.execute(
            select(Invoice).where(
                Invoice.invoice_number == invoice_number,
                Invoice.deleted_at.is_(None)
            )
        ).scalar_one_or_none()
    
    def get_statistics(self, db: Session, filters: Optional[dict] = None) -> InvoiceStatistics:
        """Get statistics"""
        query = select(Invoice).where(Invoice.deleted_at.is_(None))
        
        if filters:
            if filters.get('supplier_id'):
                query = query.where(Invoice.supplier_id == filters['supplier_id'])
        
        invoices = db.execute(query).scalars().all()
        
        return InvoiceStatistics(
            total=len(invoices),
            total_amount=sum(inv.total_amount for inv in invoices),
            paid_amount=sum(inv.paid_amount for inv in invoices),
            balance_due=sum(inv.balance_due for inv in invoices),
            by_status={},
            overdue_count=sum(1 for inv in invoices if inv.is_overdue)
        )


# ── Missing methods required by router ──────────────────────
def approve(self, db, invoice_id: int, user_id: int):
    """Mark invoice as approved + update budget spent_amount."""
    invoice = self.get_by_id_or_404(db, invoice_id)
    invoice.status = 'APPROVED'
    import datetime
    invoice.approved_at = datetime.datetime.now()
    invoice.approved_by = user_id
    db.commit()
    db.refresh(invoice)
    # Update budget
    if invoice.project_id:
        _update_budget_spent(db, invoice.project_id)
    # Audit log
    _audit(db, user_id, 'invoices', invoice.id, 'APPROVE', {'status': 'APPROVED'})
    return invoice

def send_to_supplier(self, db, invoice_id: int, user_id: int):
    """Mark invoice as sent to supplier."""
    invoice = self.get_by_id_or_404(db, invoice_id)
    invoice.status = 'sent'
    db.commit()
    db.refresh(invoice)
    return invoice


# ── Budget helpers ────────────────────────────────────────────────────────────

def _update_budget_spent(db, project_id: int):
    """Recalculate and update budget.spent_amount from approved invoices."""
    import logging
    log = logging.getLogger(__name__)
    try:
        from sqlalchemy import text
        from app.models.budget import Budget
        # Sum all APPROVED invoices for the project
        result = db.execute(text("""
            SELECT COALESCE(SUM(total_amount), 0) as total
            FROM invoices
            WHERE project_id = :pid AND UPPER(status) = 'APPROVED'
              AND deleted_at IS NULL AND is_active = true
        """), {"pid": project_id}).scalar()
        budget = db.query(Budget).filter(
            Budget.project_id == project_id, Budget.is_active == True
        ).first()
        if budget:
            budget.spent_amount = result
            db.commit()
            # Budget alert if > 90%
            if budget.total_amount and budget.total_amount > 0:
                pct = float(result) / float(budget.total_amount) * 100
                if pct >= 90:
                    _send_budget_alert(db, project_id, pct, budget.id)
    except Exception as e:
        log.warning(f"update_budget_spent failed for project {project_id}: {e}")


def _send_budget_alert(db, project_id: int, pct: float, budget_id: int):
    """Send BUDGET_ALERT notification to area manager and region manager."""
    import logging, json
    log = logging.getLogger(__name__)
    try:
        from sqlalchemy import text
        from app.services.notification_service import notification_service
        from app.schemas.notification import NotificationCreate

        # Get project name + manager ids
        row = db.execute(text("""
            SELECT p.name, p.manager_id, u.region_id, u.area_id
            FROM projects p LEFT JOIN users u ON p.manager_id = u.id
            WHERE p.id = :pid
        """), {"pid": project_id}).first()
        if not row:
            return
        project_name = row[0]
        recipient_ids = set()
        if row[1]: recipient_ids.add(row[1])  # project manager

        # Also notify region/area managers
        area_managers = db.execute(text("""
            SELECT DISTINCT u.id FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.code IN ('AREA_MANAGER','REGION_MANAGER','ADMIN')
              AND u.is_active = true
              AND (u.area_id = :aid OR u.region_id = :rid)
        """), {"aid": row[3], "rid": row[2]}).fetchall()
        for m in area_managers:
            recipient_ids.add(m[0])

        for uid in recipient_ids:
            notif = NotificationCreate(
                user_id=uid,
                title=f"⚠️ חריגת תקציב — {project_name}",
                message=f"הפרויקט {project_name} הגיע ל-{pct:.0f}% מהתקציב המאושר.",
                notification_type="BUDGET_ALERT",
                priority="high",
                channel="in_app",
                entity_type="budget",
                entity_id=budget_id,
                data=json.dumps({"project_id": project_id, "pct": pct}),
                action_url=f"/projects/{project_id}",
            )
            notification_service.create_notification(db, notif)
    except Exception as e:
        log.warning(f"Budget alert notification failed: {e}")


def _audit(db, user_id, table_name: str, record_id: int, action: str, new_values: dict):
    """Insert a row into audit_logs (best-effort)."""
    import logging, json
    try:
        from sqlalchemy import text
        db.execute(text("""
            INSERT INTO audit_logs (user_id, table_name, record_id, action, new_values)
            VALUES (:uid, :tbl, :rid, :act, :nv::jsonb)
        """), {
            "uid": user_id,
            "tbl": table_name,
            "rid": record_id,
            "act": action,
            "nv": json.dumps(new_values),
        })
        db.commit()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Audit log failed [{table_name}/{action}]: {e}")


def _notify_accountants_invoice(db, invoice_id: int, invoice_number: str, project_name: str = ""):
    """Notify all accountant-role users about a new pending invoice."""
    import logging, json
    log = logging.getLogger(__name__)
    try:
        from sqlalchemy import text
        from app.services.notification_service import notification_service
        from app.schemas.notification import NotificationCreate

        accountants = db.execute(text("""
            SELECT u.id FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.code IN ('ACCOUNTANT','ADMIN') AND u.is_active = true
        """)).fetchall()

        for row in accountants:
            notif = NotificationCreate(
                user_id=row[0],
                title=f"חשבונית חדשה ממתינה לאישור — {invoice_number}",
                message=f"חשבונית {invoice_number} {('בפרויקט ' + project_name) if project_name else ''} ממתינה לאישורך.",
                notification_type="INVOICE_PENDING",
                priority="medium",
                channel="in_app",
                entity_type="invoice",
                entity_id=invoice_id,
                data=json.dumps({"invoice_id": invoice_id}),
                action_url=f"/invoices/{invoice_id}",
            )
            notification_service.create_notification(db, notif)
    except Exception as e:
        log.warning(f"Invoice notification failed: {e}")


# ── Monthly Invoice Generator ──────────────────────────────────────────────────

def generate_monthly_invoice(
    supplier_id: int,
    project_id: int,
    month: int,
    year: int,
    created_by: int,
    db: Session,
) -> Invoice:
    """
    מרכזת כל worklogs APPROVED של ספק+פרויקט לחודש → חשבונית DRAFT.
    מקבצת לפי equipment_id (מספר רישוי).
    """
    from sqlalchemy import extract
    from app.models.worklog import Worklog
    from app.models.invoice_item import InvoiceItem

    worklogs = (
        db.query(Worklog)
        .filter(
            Worklog.supplier_id == supplier_id,
            Worklog.project_id == project_id,
            Worklog.status == "APPROVED",
            extract("month", Worklog.work_date) == month,
            extract("year", Worklog.work_date) == year,
        )
        .all()
    )

    if not worklogs:
        raise ValueError(
            f"אין דיווחים מאושרים לספק {supplier_id} / פרויקט {project_id} "
            f"בחודש {month}/{year}"
        )

    # קבץ לפי ציוד
    by_equipment: dict = {}
    for wl in worklogs:
        key = wl.equipment_id or 0
        by_equipment.setdefault(key, []).append(wl)

    # חשב סכום כולל
    subtotal = sum(float(wl.cost_before_vat or wl.total_amount or 0) for wl in worklogs)
    vat_pct = float(worklogs[0].vat_rate or 0.17) if worklogs else 0.17
    tax_amount = round(subtotal * vat_pct, 2)
    total_amount = round(subtotal + tax_amount, 2)

    # מספר חשבונית
    invoice_count = db.query(Invoice).count()
    invoice_number = f"INV-{year}{month:02d}-{invoice_count + 1:04d}"

    invoice = Invoice(
        invoice_number=invoice_number,
        supplier_id=supplier_id,
        project_id=project_id,
        status="DRAFT",
        created_by=created_by,
        issue_date=dt_date.today(),
        due_date=dt_date.today().replace(day=1),  # תאריך לתשלום ידני
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
    )
    db.add(invoice)
    db.flush()

    # צור invoice_items לפי ציוד
    line = 1
    for eq_id, wls in by_equipment.items():
        paid_hours_total = sum(float(w.paid_hours or w.hours_worked or 0) for w in wls)
        overnight_total = sum(float(w.overnight_total or 0) for w in wls)
        rate = float(wls[0].hourly_rate_snapshot or wls[0].hourly_rate or 0)
        item_subtotal = round(paid_hours_total * rate + overnight_total, 2)
        tax = round(item_subtotal * vat_pct, 2)

        eq_name = ""
        if wls[0].equipment:
            eq = wls[0].equipment
            eq_name = f"{getattr(eq, 'name', '')} {getattr(eq, 'license_plate', '') or ''}".strip()

        item = InvoiceItem(
            invoice_id=invoice.id,
            line_number=line,
            description=f"{eq_name} — {len(wls)} ימי עבודה",
            quantity=paid_hours_total,
            unit_price=rate,
            total_price=item_subtotal,
            discount_percent=0,
            discount_amount=0,
            subtotal=item_subtotal,
            tax_rate=vat_pct,
            tax_amount=tax,
            total=item_subtotal + tax,
            equipment_type_id=getattr(wls[0].equipment, 'equipment_type_id', None) if wls[0].equipment else None,
        )
        db.add(item)
        line += 1

        # סמן worklogs כ-INVOICED
        for wl in wls:
            wl.status = "INVOICED"

    # שחרר הקפאת תקציב
    try:
        from app.services.budget_service import release_budget_freeze
        # מחפש work_order_id מהראשון שיש לו
        wo_ids = list({wl.work_order_id for wl in worklogs if wl.work_order_id})
        for wo_id in wo_ids:
            release_budget_freeze(wo_id, 0, db)  # actual amount יחושב מהחשבונית
    except Exception:
        pass

    db.commit()
    db.refresh(invoice)
    return invoice


def get_uninvoiced_suppliers(project_id: int, month: int, year: int, db: Session) -> list:
    """
    מחזיר רשימת ספקים עם דיווחים מאושרים שלא שויכו לחשבונית בחודש נתון.
    """
    from sqlalchemy import extract
    from app.models.worklog import Worklog

    rows = (
        db.query(Worklog.supplier_id, Worklog.project_id)
        .filter(
            Worklog.project_id == project_id,
            Worklog.status == "APPROVED",
            extract("month", Worklog.work_date) == month,
            extract("year", Worklog.work_date) == year,
        )
        .distinct()
        .all()
    )
    return [{"supplier_id": r.supplier_id, "project_id": r.project_id} for r in rows]


# ── Endpoint registration helper ──────────────────────────────────────────────
# ה-endpoint נרשם ב-invoices.py עצמו (ראה שלב הבא)
