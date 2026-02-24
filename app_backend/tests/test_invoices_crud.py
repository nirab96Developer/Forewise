"""
Invoice CRUD Tests
"""

import pytest
import time
from datetime import date, timedelta
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.invoice import Invoice
from app.models.supplier import Supplier
from app.models.project import Project
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceSearch
from app.services.invoice_service import InvoiceService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def invoice_service():
    return InvoiceService()


@pytest.fixture
def test_data(db):
    """Get valid IDs"""
    supplier = db.query(Supplier).filter(Supplier.is_active == True).first()
    project = db.query(Project).filter(Project.is_active == True).first()
    
    return {
        'supplier_id': supplier.id if supplier else 1,
        'project_id': project.id if project else 1,
        'user_id': 4
    }


class TestInvoiceCRUD:
    
    def test_01_create(self, db, invoice_service, test_data):
        """Create with timestamps"""
        inv = invoice_service.create(db, InvoiceCreate(
            invoice_number=f"INV-{int(time.time())}",
            supplier_id=test_data['supplier_id'],
            project_id=test_data['project_id'],
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170')
        ), test_data['user_id'])
        
        assert inv.id is not None
        assert inv.created_at is not None
        assert inv.updated_at is not None
        
        db.delete(inv)
        db.commit()
    
    def test_02_get(self, db, invoice_service, test_data):
        """Get by ID"""
        inv = invoice_service.create(db, InvoiceCreate(
            invoice_number=f"INV-{int(time.time())}",
            supplier_id=test_data['supplier_id'],
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170')
        ), test_data['user_id'])
        
        fetched = invoice_service.get_by_id(db, inv.id)
        assert fetched is not None
        
        db.delete(inv)
        db.commit()
    
    def test_03_update_trigger(self, db, invoice_service, test_data):
        """Update + trigger"""
        inv = invoice_service.create(db, InvoiceCreate(
            invoice_number=f"INV-{int(time.time())}",
            supplier_id=test_data['supplier_id'],
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170')
        ), test_data['user_id'])
        
        fu = inv.updated_at
        time.sleep(2)
        
        upd = invoice_service.update(db, inv.id, InvoiceUpdate(notes="Updated notes"), test_data['user_id'])
        assert upd.updated_at > fu, "Trigger should work"
        
        db.delete(inv)
        db.commit()
    
    def test_04_list(self, db, invoice_service, test_data):
        """List with pagination"""
        inv = invoice_service.create(db, InvoiceCreate(
            invoice_number=f"INV-{int(time.time())}",
            supplier_id=test_data['supplier_id'],
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170')
        ), test_data['user_id'])
        
        items, total = invoice_service.list(db, InvoiceSearch())
        assert total >= 1
        
        db.delete(inv)
        db.commit()
    
    def test_05_by_number(self, db, invoice_service, test_data):
        """Get by number"""
        num = f"INV-{int(time.time())}"
        inv = invoice_service.create(db, InvoiceCreate(
            invoice_number=num,
            supplier_id=test_data['supplier_id'],
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170')
        ), test_data['user_id'])
        
        found = invoice_service.get_by_number(db, num)
        assert found is not None
        assert found.id == inv.id
        
        db.delete(inv)
        db.commit()
    
    def test_06_soft_delete(self, db, invoice_service, test_data):
        """Soft delete"""
        inv = invoice_service.create(db, InvoiceCreate(
            invoice_number=f"INV-{int(time.time())}",
            supplier_id=test_data['supplier_id'],
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170')
        ), test_data['user_id'])
        
        i, t = invoice_service.list(db, InvoiceSearch())
        deleted = invoice_service.soft_delete(db, inv.id, test_data['user_id'])
        i2, t2 = invoice_service.list(db, InvoiceSearch())
        assert t2 < t
        
        db.delete(inv)
        db.commit()
    
    def test_07_restore(self, db, invoice_service, test_data):
        """Restore"""
        inv = invoice_service.create(db, InvoiceCreate(
            invoice_number=f"INV-{int(time.time())}",
            supplier_id=test_data['supplier_id'],
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170')
        ), test_data['user_id'])
        
        invoice_service.soft_delete(db, inv.id, test_data['user_id'])
        i, t = invoice_service.list(db, InvoiceSearch())
        
        restored = invoice_service.restore(db, inv.id, test_data['user_id'])
        i2, t2 = invoice_service.list(db, InvoiceSearch())
        assert t2 > t
        
        db.delete(inv)
        db.commit()
    
    def test_08_unique_invoice_number(self, db, invoice_service, test_data):
        """UNIQUE invoice_number"""
        num = f"INV-{int(time.time())}"
        inv = invoice_service.create(db, InvoiceCreate(
            invoice_number=num,
            supplier_id=test_data['supplier_id'],
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000'),
            tax_amount=Decimal('170'),
            total_amount=Decimal('1170')
        ), test_data['user_id'])
        
        from app.core.exceptions import DuplicateException
        with pytest.raises(DuplicateException):
            invoice_service.create(db, InvoiceCreate(
                invoice_number=num,
                supplier_id=test_data['supplier_id'],
                issue_date=date.today(),
                due_date=date.today() + timedelta(days=30),
                subtotal=Decimal('500'),
                tax_amount=Decimal('85'),
                total_amount=Decimal('585')
            ), test_data['user_id'])
        
        db.delete(inv)
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
