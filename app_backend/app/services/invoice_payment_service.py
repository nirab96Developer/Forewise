"""
InvoicePayment Service
"""

from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.invoice_payment import InvoicePayment
from app.models.invoice import Invoice
from app.schemas.invoice_payment import InvoicePaymentCreate, InvoicePaymentUpdate, InvoicePaymentSearch
from app.core.exceptions import NotFoundException, ValidationException, DuplicateException


class InvoicePaymentService:
    """InvoicePayment Service - TRANSACTIONS (but DB has deleted_at/version)"""
    
    def create(self, db: Session, data: InvoicePaymentCreate, current_user_id: int) -> InvoicePayment:
        """Create payment"""
        # Validate FK: invoice_id
        invoice = db.query(Invoice).filter_by(id=data.invoice_id).first()
        if not invoice:
            raise ValidationException(f"Invoice {data.invoice_id} not found")
        if not invoice.is_active:
            raise ValidationException(f"Invoice {data.invoice_id} is not active")
        
        # Create
        payment_dict = data.model_dump(exclude_unset=True)
        payment_dict['processed_by'] = current_user_id
        
        payment = InvoicePayment(**payment_dict)
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment
    
    def get_by_id(self, db: Session, payment_id: int) -> Optional[InvoicePayment]:
        """Get payment"""
        return db.query(InvoicePayment).filter_by(id=payment_id).first()
    
    def update(self, db: Session, payment_id: int, data: InvoicePaymentUpdate, current_user_id: int) -> InvoicePayment:
        """Update payment"""
        payment = self.get_by_id(db, payment_id)
        if not payment:
            raise NotFoundException(f"Payment {payment_id} not found")
        
        # Version check
        if data.version is not None and payment.version != data.version:
            raise DuplicateException("Payment was modified by another user")
        
        update_dict = data.model_dump(exclude_unset=True, exclude={'version'})
        
        for field, value in update_dict.items():
            setattr(payment, field, value)
        
        if payment.version is not None:
            payment.version += 1
        
        db.commit()
        db.refresh(payment)
        return payment
    
    def list(self, db: Session, search: InvoicePaymentSearch) -> Tuple[List[InvoicePayment], int]:
        """List payments"""
        query = db.query(InvoicePayment)
        
        # Filter deleted if using deleted_at
        if not search.include_deleted:
            query = query.filter(InvoicePayment.deleted_at.is_(None))
        
        # Active filter
        if search.is_active is not None:
            query = query.filter(InvoicePayment.is_active == search.is_active)
        elif search.is_active is None:
            query = query.filter(InvoicePayment.is_active == True)
        
        # Filters
        if search.invoice_id:
            query = query.filter(InvoicePayment.invoice_id == search.invoice_id)
        if search.payment_method:
            query = query.filter(InvoicePayment.payment_method == search.payment_method)
        if search.date_from:
            query = query.filter(InvoicePayment.payment_date >= search.date_from)
        if search.date_to:
            query = query.filter(InvoicePayment.payment_date <= search.date_to)
        
        total = query.count()
        
        # Sort
        sort_col = getattr(InvoicePayment, search.sort_by, InvoicePayment.payment_date)
        query = query.order_by(sort_col.desc() if search.sort_desc else sort_col.asc())
        
        # Paginate
        offset = (search.page - 1) * search.page_size
        payments = query.offset(offset).limit(search.page_size).all()
        
        return payments, total
    
    def deactivate(self, db: Session, payment_id: int, current_user_id: int) -> InvoicePayment:
        """Deactivate payment (TRANSACTIONS pattern)"""
        payment = self.get_by_id(db, payment_id)
        if not payment:
            raise NotFoundException(f"Payment {payment_id} not found")
        
        payment.is_active = False
        db.commit()
        db.refresh(payment)
        return payment
    
    def activate(self, db: Session, payment_id: int, current_user_id: int) -> InvoicePayment:
        """Activate payment"""
        payment = db.query(InvoicePayment).filter_by(id=payment_id).first()
        if not payment:
            raise NotFoundException(f"Payment {payment_id} not found")
        
        payment.is_active = True
        db.commit()
        db.refresh(payment)
        return payment
