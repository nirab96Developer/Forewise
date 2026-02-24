"""
InvoicePayment CRUD Tests
"""

import pytest
import time
from datetime import date, timedelta
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.invoice_payment import InvoicePayment
from app.models.invoice import Invoice
from app.models.supplier import Supplier
from app.schemas.invoice_payment import InvoicePaymentCreate, InvoicePaymentUpdate, InvoicePaymentSearch
from app.services.invoice_payment_service import InvoicePaymentService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def invoice_payment_service():
    return InvoicePaymentService()


@pytest.fixture
def test_invoice(db):
    """Create test invoice"""
    supplier = db.query(Supplier).filter(Supplier.is_active == True).first()
    invoice = Invoice(
        invoice_number=f"INV-{int(time.time())}",
        supplier_id=supplier.id,
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        subtotal=Decimal('1000'),
        tax_amount=Decimal('170'),
        total_amount=Decimal('1170'),
        paid_amount=Decimal('0'),
        status="APPROVED"
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


class TestInvoicePaymentCRUD:
    
    def test_01_create(self, db, invoice_payment_service, test_invoice):
        """Create"""
        payment = invoice_payment_service.create(db, InvoicePaymentCreate(
            invoice_id=test_invoice.id,
            payment_date=date.today(),
            amount=Decimal('500'),
            payment_method="BANK_TRANSFER"
        ), 4)
        assert payment.id is not None
        assert payment.created_at is not None
        db.delete(payment)
        db.delete(test_invoice)
        db.commit()
    
    def test_02_get(self, db, invoice_payment_service, test_invoice):
        """Get"""
        payment = invoice_payment_service.create(db, InvoicePaymentCreate(
            invoice_id=test_invoice.id,
            payment_date=date.today(),
            amount=Decimal('500'),
            payment_method="CASH"
        ), 4)
        fetched = invoice_payment_service.get_by_id(db, payment.id)
        assert fetched is not None
        db.delete(payment)
        db.delete(test_invoice)
        db.commit()
    
    def test_03_update_trigger(self, db, invoice_payment_service, test_invoice):
        """Update + trigger"""
        payment = invoice_payment_service.create(db, InvoicePaymentCreate(
            invoice_id=test_invoice.id,
            payment_date=date.today(),
            amount=Decimal('500'),
            payment_method="CASH"
        ), 4)
        fu = payment.updated_at
        time.sleep(2)
        upd = invoice_payment_service.update(db, payment.id, InvoicePaymentUpdate(notes="Updated"), 4)
        assert upd.updated_at > fu
        db.delete(payment)
        db.delete(test_invoice)
        db.commit()
    
    def test_04_list(self, db, invoice_payment_service, test_invoice):
        """List"""
        payment = invoice_payment_service.create(db, InvoicePaymentCreate(
            invoice_id=test_invoice.id,
            payment_date=date.today(),
            amount=Decimal('500'),
            payment_method="CASH"
        ), 4)
        items, total = invoice_payment_service.list(db, InvoicePaymentSearch())
        assert total >= 1
        db.delete(payment)
        db.delete(test_invoice)
        db.commit()
    
    def test_05_filter_by_invoice(self, db, invoice_payment_service, test_invoice):
        """Filter by invoice_id"""
        payment = invoice_payment_service.create(db, InvoicePaymentCreate(
            invoice_id=test_invoice.id,
            payment_date=date.today(),
            amount=Decimal('500'),
            payment_method="CASH"
        ), 4)
        items, total = invoice_payment_service.list(db, InvoicePaymentSearch(invoice_id=test_invoice.id))
        assert any(p.id == payment.id for p in items)
        db.delete(payment)
        db.delete(test_invoice)
        db.commit()
    
    def test_06_deactivate(self, db, invoice_payment_service, test_invoice):
        """Deactivate"""
        payment = invoice_payment_service.create(db, InvoicePaymentCreate(
            invoice_id=test_invoice.id,
            payment_date=date.today(),
            amount=Decimal('500'),
            payment_method="CASH"
        ), 4)
        i, t = invoice_payment_service.list(db, InvoicePaymentSearch())
        deactivated = invoice_payment_service.deactivate(db, payment.id, 4)
        i2, t2 = invoice_payment_service.list(db, InvoicePaymentSearch())
        assert t2 < t
        db.delete(payment)
        db.delete(test_invoice)
        db.commit()
    
    def test_07_activate(self, db, invoice_payment_service, test_invoice):
        """Activate"""
        payment = invoice_payment_service.create(db, InvoicePaymentCreate(
            invoice_id=test_invoice.id,
            payment_date=date.today(),
            amount=Decimal('500'),
            payment_method="CASH"
        ), 4)
        invoice_payment_service.deactivate(db, payment.id, 4)
        i, t = invoice_payment_service.list(db, InvoicePaymentSearch())
        activated = invoice_payment_service.activate(db, payment.id, 4)
        i2, t2 = invoice_payment_service.list(db, InvoicePaymentSearch())
        assert t2 > t
        db.delete(payment)
        db.delete(test_invoice)
        db.commit()
    
    def test_08_fk_validation(self, db, invoice_payment_service):
        """FK validation"""
        from app.core.exceptions import ValidationException
        with pytest.raises(ValidationException):
            invoice_payment_service.create(db, InvoicePaymentCreate(
                invoice_id=999999,
                payment_date=date.today(),
                amount=Decimal('500'),
                payment_method="CASH"
            ), 4)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
