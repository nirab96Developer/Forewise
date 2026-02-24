"""
Integration Test: Invoice → Items → Payments Flow
Verifies complete financial flow works together
"""

import pytest
import time
from datetime import date, timedelta
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.supplier import Supplier
from app.schemas.invoice import InvoiceCreate
from app.schemas.invoice_item import InvoiceItemCreate, InvoiceItemSearch
from app.schemas.invoice_payment import InvoicePaymentCreate, InvoicePaymentSearch
from app.services.invoice_service import InvoiceService
from app.services.invoice_item_service import InvoiceItemService
from app.services.invoice_payment_service import InvoicePaymentService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_supplier(db):
    """Get active supplier"""
    supplier = db.query(Supplier).filter(Supplier.is_active == True).first()
    return supplier


class TestInvoiceFullFlowIntegration:
    """Invoice → Items → Payments complete flow"""
    
    def test_01_create_invoice(self, db, test_supplier):
        """Create invoice"""
        invoice_service = InvoiceService()
        
        invoice = invoice_service.create(db, InvoiceCreate(
            invoice_number=f"INT-{int(time.time())}",
            supplier_id=test_supplier.id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170'),
            status="PENDING"
        ), 4)
        
        assert invoice.id is not None
        
        # Cleanup
        db.delete(invoice)
        db.commit()
    
    def test_02_create_items_under_invoice(self, db, test_supplier):
        """Create 2 items under invoice"""
        invoice_service = InvoiceService()
        item_service = InvoiceItemService()
        
        invoice = invoice_service.create(db, InvoiceCreate(
            invoice_number=f"INT-{int(time.time())}",
            supplier_id=test_supplier.id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170'),
            status="PENDING"
        ), 4)
        
        item1 = item_service.create(db, InvoiceItemCreate(
            invoice_id=invoice.id,
            line_number=1,
            description="Item 1",
            quantity=Decimal('2'),
            unit_price=Decimal('400'),
            subtotal=Decimal('800'),
            tax_amount=Decimal('136'),
            total=Decimal('936')
        ), 4)
        
        item2 = item_service.create(db, InvoiceItemCreate(
            invoice_id=invoice.id,
            line_number=2,
            description="Item 2",
            quantity=Decimal('1'),
            unit_price=Decimal('200'),
            subtotal=Decimal('200'),
            tax_amount=Decimal('34'),
            total=Decimal('234')
        ), 4)
        
        assert item1.invoice_id == invoice.id
        assert item2.invoice_id == invoice.id
        
        # Cleanup
        db.delete(item1)
        db.delete(item2)
        db.delete(invoice)
        db.commit()
    
    def test_03_create_payment_for_invoice(self, db, test_supplier):
        """Create payment for invoice"""
        invoice_service = InvoiceService()
        payment_service = InvoicePaymentService()
        
        invoice = invoice_service.create(db, InvoiceCreate(
            invoice_number=f"INT-{int(time.time())}",
            supplier_id=test_supplier.id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170'),
            status="APPROVED"
        ), 4)
        
        payment = payment_service.create(db, InvoicePaymentCreate(
            invoice_id=invoice.id,
            payment_date=date.today(),
            amount=Decimal('500'),
            payment_method="BANK_TRANSFER"
        ), 4)
        
        assert payment.invoice_id == invoice.id
        assert payment.is_active == True
        
        # Cleanup
        db.delete(payment)
        db.delete(invoice)
        db.commit()
    
    def test_04_list_items_by_invoice(self, db, test_supplier):
        """List items filtered by invoice_id"""
        invoice_service = InvoiceService()
        item_service = InvoiceItemService()
        
        invoice = invoice_service.create(db, InvoiceCreate(
            invoice_number=f"INT-{int(time.time())}",
            supplier_id=test_supplier.id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170'),
            status="PENDING"
        ), 4)
        
        item1 = item_service.create(db, InvoiceItemCreate(
            invoice_id=invoice.id,
            line_number=1,
            description="Item 1",
            quantity=Decimal('1'),
            unit_price=Decimal('500'),
            subtotal=Decimal('500'),
            tax_amount=Decimal('85'),
            total=Decimal('585')
        ), 4)
        
        item2 = item_service.create(db, InvoiceItemCreate(
            invoice_id=invoice.id,
            line_number=2,
            description="Item 2",
            quantity=Decimal('1'),
            unit_price=Decimal('500'),
            subtotal=Decimal('500'),
            tax_amount=Decimal('85'),
            total=Decimal('585')
        ), 4)
        
        # List items
        items, total = item_service.list(db, InvoiceItemSearch(invoice_id=invoice.id))
        
        assert total == 2
        assert all(i.invoice_id == invoice.id for i in items)
        
        # Cleanup
        db.delete(item1)
        db.delete(item2)
        db.delete(invoice)
        db.commit()
    
    def test_05_list_payments_by_invoice(self, db, test_supplier):
        """List payments filtered by invoice_id"""
        invoice_service = InvoiceService()
        payment_service = InvoicePaymentService()
        
        invoice = invoice_service.create(db, InvoiceCreate(
            invoice_number=f"INT-{int(time.time())}",
            supplier_id=test_supplier.id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170'),
            status="APPROVED"
        ), 4)
        
        payment = payment_service.create(db, InvoicePaymentCreate(
            invoice_id=invoice.id,
            payment_date=date.today(),
            amount=Decimal('500'),
            payment_method="CASH"
        ), 4)
        
        # List payments
        payments, total = payment_service.list(db, InvoicePaymentSearch(invoice_id=invoice.id))
        
        assert total == 1
        assert payments[0].invoice_id == invoice.id
        
        # Cleanup
        db.delete(payment)
        db.delete(invoice)
        db.commit()
    
    def test_06_update_invoice_trigger(self, db, test_supplier):
        """Update invoice + verify trigger works"""
        invoice_service = InvoiceService()
        
        invoice = invoice_service.create(db, InvoiceCreate(
            invoice_number=f"INT-{int(time.time())}",
            supplier_id=test_supplier.id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170'),
            status="PENDING"
        ), 4)
        
        fu = invoice.updated_at
        time.sleep(2)
        
        from app.schemas.invoice import InvoiceUpdate
        updated = invoice_service.update(db, invoice.id, InvoiceUpdate(notes="Integration test"), 4)
        
        assert updated.updated_at > fu, "Trigger should work"
        
        # Cleanup
        db.delete(invoice)
        db.commit()
    
    def test_07_deactivate_payment(self, db, test_supplier):
        """Deactivate payment filters from list"""
        invoice_service = InvoiceService()
        payment_service = InvoicePaymentService()
        
        invoice = invoice_service.create(db, InvoiceCreate(
            invoice_number=f"INT-{int(time.time())}",
            supplier_id=test_supplier.id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170'),
            status="APPROVED"
        ), 4)
        
        payment = payment_service.create(db, InvoicePaymentCreate(
            invoice_id=invoice.id,
            payment_date=date.today(),
            amount=Decimal('500'),
            payment_method="CASH"
        ), 4)
        
        # List before
        payments_before, total_before = payment_service.list(db, InvoicePaymentSearch(invoice_id=invoice.id))
        
        # Deactivate
        payment_service.deactivate(db, payment.id, 4)
        
        # List after
        payments_after, total_after = payment_service.list(db, InvoicePaymentSearch(invoice_id=invoice.id))
        
        assert total_after < total_before, "Deactivated payment should be filtered"
        
        # Cleanup
        db.delete(payment)
        db.delete(invoice)
        db.commit()
    
    def test_08_activate_payment(self, db, test_supplier):
        """Activate payment returns to list"""
        invoice_service = InvoiceService()
        payment_service = InvoicePaymentService()
        
        invoice = invoice_service.create(db, InvoiceCreate(
            invoice_number=f"INT-{int(time.time())}",
            supplier_id=test_supplier.id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170'),
            status="APPROVED"
        ), 4)
        
        payment = payment_service.create(db, InvoicePaymentCreate(
            invoice_id=invoice.id,
            payment_date=date.today(),
            amount=Decimal('500'),
            payment_method="CASH"
        ), 4)
        
        # Deactivate
        payment_service.deactivate(db, payment.id, 4)
        payments_deact, total_deact = payment_service.list(db, InvoicePaymentSearch(invoice_id=invoice.id))
        
        # Activate
        payment_service.activate(db, payment.id, 4)
        payments_act, total_act = payment_service.list(db, InvoicePaymentSearch(invoice_id=invoice.id))
        
        assert total_act > total_deact, "Activated payment should return to list"
        
        # Cleanup
        db.delete(payment)
        db.delete(invoice)
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
