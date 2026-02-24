"""
Invoice Service
"""

from typing import Optional, List, Tuple
from decimal import Decimal
from datetime import date
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.models.invoice import Invoice
from app.models.supplier import Supplier
from app.models.project import Project
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceSearch, InvoiceStatistics
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException
from app.services import activity_logger


class InvoiceService(BaseService[Invoice]):
    """Invoice Service - CORE"""

    def __init__(self):
        super().__init__(Invoice)

    def create(self, db: Session, data: InvoiceCreate, current_user_id: int) -> Invoice:
        """Create invoice"""
        # Validate FK: supplier_id
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
            if not project.is_active:
                raise ValidationException(f"Project {data.project_id} is not active")

        # Validate UNIQUE: invoice_number
        existing = db.query(Invoice).filter(
            Invoice.invoice_number == data.invoice_number,
            Invoice.deleted_at.is_(None)
        ).first()
        if existing:
            raise DuplicateException(f"Invoice number '{data.invoice_number}' already exists")

        # Create
        invoice_dict = data.model_dump(exclude_unset=True)
        invoice_dict['created_by'] = current_user_id

        # Ensure status has default if not provided
        if 'status' not in invoice_dict or not invoice_dict['status']:
            invoice_dict['status'] = 'DRAFT'

        invoice = Invoice(**invoice_dict)
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        # Log activity
        activity_logger.log_invoice_created(
            db=db,
            invoice_id=invoice.id,
            user_id=current_user_id,
            supplier_id=data.supplier_id,
            work_order_id=None,
        )

        return invoice

    def update(self, db: Session, invoice_id: int, data: InvoiceUpdate, current_user_id: int) -> Invoice:
        """Update invoice"""
        invoice = self.get_by_id_or_404(db, invoice_id)

        # Version check
        if data.version is not None and invoice.version != data.version:
            raise DuplicateException("Invoice was modified by another user")

        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})

        # Validate UNIQUE: invoice_number (if changed)
        if 'invoice_number' in update_dict and update_dict['invoice_number'] != invoice.invoice_number:
            existing = db.query(Invoice).filter(
                Invoice.invoice_number == update_dict['invoice_number'],
                Invoice.id != invoice_id,
                Invoice.deleted_at.is_(None)
            ).first()
            if existing:
                raise DuplicateException(
                    f"Invoice number '{update_dict['invoice_number']}' already exists")

        # Validate FK: supplier_id (if changed)
        if 'supplier_id' in update_dict:
            supplier = db.query(Supplier).filter_by(id=update_dict['supplier_id']).first()
            if not supplier:
                raise ValidationException(f"Supplier {update_dict['supplier_id']} not found")

        # Validate FK: project_id (if changed)
        if 'project_id' in update_dict and update_dict['project_id']:
            project = db.query(Project).filter_by(id=update_dict['project_id']).first()
            if not project:
                raise ValidationException(f"Project {update_dict['project_id']} not found")

        # Update
        for field, value in update_dict.items():
            setattr(invoice, field, value)

        # Keep compatibility when DB trigger is missing in drifted environments.
        invoice.updated_at = datetime.utcnow()

        if invoice.version is not None:
            invoice.version += 1

        db.commit()
        db.refresh(invoice)
        return invoice

    def list(self, db: Session, search: InvoiceSearch) -> Tuple[List[Invoice], int]:
        """List invoices"""
        query = self._base_query(db, include_deleted=search.include_deleted)

        # Free text search
        if search.q:
            term = f"%{search.q}%"
            query = query.where(or_(
                Invoice.invoice_number.ilike(term),
                Invoice.notes.ilike(term)
            ))

        # Filters
        if search.supplier_id:
            query = query.where(Invoice.supplier_id == search.supplier_id)
        if search.project_id:
            query = query.where(Invoice.project_id == search.project_id)
        if search.area_id is not None:
            area_project_ids = select(Project.id).where(Project.area_id == search.area_id)
            query = query.where(Invoice.project_id.in_(area_project_ids))
        if search.status:
            query = query.where(Invoice.status == search.status.value)
        if search.issue_date_from:
            query = query.where(Invoice.issue_date >= search.issue_date_from)
        if search.issue_date_to:
            query = query.where(Invoice.issue_date <= search.issue_date_to)
        if search.due_date_from:
            query = query.where(Invoice.due_date >= search.due_date_from)
        if search.due_date_to:
            query = query.where(Invoice.due_date <= search.due_date_to)
        if search.min_total:
            query = query.where(Invoice.total_amount >= search.min_total)
        if search.max_total:
            query = query.where(Invoice.total_amount <= search.max_total)
        if search.is_active is not None:
            query = query.where(Invoice.is_active == search.is_active)

        # Count
        total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

        # Sort
        sort_col = getattr(Invoice, search.sort_by, Invoice.issue_date)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())

        # Paginate
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
            if filters.get('project_id'):
                query = query.where(Invoice.project_id == filters['project_id'])

        invoices = db.execute(query).scalars().all()

        # Calculate
        total_amount = sum(inv.total_amount for inv in invoices)
        paid_amount = sum(inv.paid_amount for inv in invoices)
        balance = total_amount - paid_amount

        # By status
        by_status = {}
        for inv in invoices:
            by_status[inv.status] = by_status.get(inv.status, 0) + 1

        # Overdue count
        today = date.today()
        overdue = sum(1 for inv in invoices if inv.due_date
                      < today and inv.paid_amount < inv.total_amount)

        return InvoiceStatistics(
            total=len(invoices),
            total_amount=total_amount,
            paid_amount=paid_amount,
            balance_due=balance,
            by_status=by_status,
            overdue_count=overdue
        )

    def approve(self, db: Session, invoice_id: int, current_user_id: int) -> Invoice:
        """Approve invoice"""
        invoice = self.get_by_id_or_404(db, invoice_id)

        invoice.status = 'APPROVED'

        if invoice.version is not None:
            invoice.version += 1

        db.commit()
        db.refresh(invoice)

        # Log activity
        activity_logger.log_invoice_approved(
            db=db,
            invoice_id=invoice.id,
            user_id=current_user_id,
            approved_by_id=current_user_id,
            supplier_id=invoice.supplier_id
        )

        return invoice

    def send_to_supplier(self, db: Session, invoice_id: int, current_user_id: int) -> Invoice:
        """Mark invoice as sent to supplier"""
        invoice = self.get_by_id_or_404(db, invoice_id)

        invoice.status = 'SENT'

        if invoice.version is not None:
            invoice.version += 1

        db.commit()
        db.refresh(invoice)

        # Log activity
        activity_logger.log_invoice_sent_to_supplier(
            db=db,
            invoice_id=invoice.id,
            user_id=current_user_id,
            supplier_id=invoice.supplier_id
        )

        return invoice
