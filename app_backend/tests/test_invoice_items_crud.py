"""
InvoiceItem CRUD Tests
"""

import pytest
import time
from datetime import date, timedelta
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.invoice_item import InvoiceItem
from app.models.invoice import Invoice
from app.models.supplier import Supplier
from app.schemas.invoice_item import InvoiceItemCreate, InvoiceItemUpdate, InvoiceItemSearch
from app.services.invoice_item_service import InvoiceItemService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def invoice_item_service():
    return InvoiceItemService()


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
        status="PENDING"
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


class TestInvoiceItemCRUD:
    
    def test_01_create(self, db, invoice_item_service, test_invoice):
        """Create"""
        item = invoice_item_service.create(db, InvoiceItemCreate(
            invoice_id=test_invoice.id,
            line_number=1,
            description="Test Item",
            quantity=Decimal('2'),
            unit_price=Decimal('100'),
            subtotal=Decimal('200'),
            tax_amount=Decimal('34'),
            total=Decimal('234')
        ), 4)
        assert item.id is not None
        assert item.created_at is not None
        db.delete(item)
        db.delete(test_invoice)
        db.commit()
    
    def test_02_get(self, db, invoice_item_service, test_invoice):
        """Get"""
        item = invoice_item_service.create(db, InvoiceItemCreate(
            invoice_id=test_invoice.id,
            line_number=1,
            description="Test",
            quantity=Decimal('1'),
            unit_price=Decimal('100'),
            subtotal=Decimal('100'),
            tax_amount=Decimal('17'),
            total=Decimal('117')
        ), 4)
        fetched = invoice_item_service.get_by_id(db, item.id)
        assert fetched is not None
        db.delete(item)
        db.delete(test_invoice)
        db.commit()
    
    def test_03_update_trigger(self, db, invoice_item_service, test_invoice):
        """Update + trigger"""
        item = invoice_item_service.create(db, InvoiceItemCreate(
            invoice_id=test_invoice.id,
            line_number=1,
            description="Test",
            quantity=Decimal('1'),
            unit_price=Decimal('100'),
            subtotal=Decimal('100'),
            tax_amount=Decimal('17'),
            total=Decimal('117')
        ), 4)
        fu = item.updated_at
        time.sleep(2)
        upd = invoice_item_service.update(db, item.id, InvoiceItemUpdate(description="Updated"), 4)
        assert upd.updated_at > fu
        db.delete(item)
        db.delete(test_invoice)
        db.commit()
    
    def test_04_list(self, db, invoice_item_service, test_invoice):
        """List"""
        item = invoice_item_service.create(db, InvoiceItemCreate(
            invoice_id=test_invoice.id,
            line_number=1,
            description="Test",
            quantity=Decimal('1'),
            unit_price=Decimal('100'),
            subtotal=Decimal('100'),
            tax_amount=Decimal('17'),
            total=Decimal('117')
        ), 4)
        items, total = invoice_item_service.list(db, InvoiceItemSearch())
        assert total >= 1
        db.delete(item)
        db.delete(test_invoice)
        db.commit()
    
    def test_05_filter_by_invoice(self, db, invoice_item_service, test_invoice):
        """Filter by invoice_id"""
        item = invoice_item_service.create(db, InvoiceItemCreate(
            invoice_id=test_invoice.id,
            line_number=1,
            description="Test",
            quantity=Decimal('1'),
            unit_price=Decimal('100'),
            subtotal=Decimal('100'),
            tax_amount=Decimal('17'),
            total=Decimal('117')
        ), 4)
        items, total = invoice_item_service.list(db, InvoiceItemSearch(invoice_id=test_invoice.id))
        assert any(i.id == item.id for i in items)
        db.delete(item)
        db.delete(test_invoice)
        db.commit()
    
    def test_06_soft_delete(self, db, invoice_item_service, test_invoice):
        """Soft delete"""
        item = invoice_item_service.create(db, InvoiceItemCreate(
            invoice_id=test_invoice.id,
            line_number=1,
            description="Test",
            quantity=Decimal('1'),
            unit_price=Decimal('100'),
            subtotal=Decimal('100'),
            tax_amount=Decimal('17'),
            total=Decimal('117')
        ), 4)
        i, t = invoice_item_service.list(db, InvoiceItemSearch())
        deleted = invoice_item_service.soft_delete(db, item.id, 4)
        i2, t2 = invoice_item_service.list(db, InvoiceItemSearch())
        assert t2 < t
        db.delete(item)
        db.delete(test_invoice)
        db.commit()
    
    def test_07_restore(self, db, invoice_item_service, test_invoice):
        """Restore"""
        item = invoice_item_service.create(db, InvoiceItemCreate(
            invoice_id=test_invoice.id,
            line_number=1,
            description="Test",
            quantity=Decimal('1'),
            unit_price=Decimal('100'),
            subtotal=Decimal('100'),
            tax_amount=Decimal('17'),
            total=Decimal('117')
        ), 4)
        invoice_item_service.soft_delete(db, item.id, 4)
        i, t = invoice_item_service.list(db, InvoiceItemSearch())
        restored = invoice_item_service.restore(db, item.id, 4)
        i2, t2 = invoice_item_service.list(db, InvoiceItemSearch())
        assert t2 > t
        db.delete(item)
        db.delete(test_invoice)
        db.commit()
    
    def test_08_fk_validation(self, db, invoice_item_service):
        """FK validation"""
        from app.core.exceptions import ValidationException
        with pytest.raises(ValidationException):
            invoice_item_service.create(db, InvoiceItemCreate(
                invoice_id=999999,
                line_number=1,
                description="Test",
                quantity=Decimal('1'),
                unit_price=Decimal('100'),
                subtotal=Decimal('100'),
                tax_amount=Decimal('17'),
                total=Decimal('117')
            ), 4)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
