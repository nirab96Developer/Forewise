"""
Supplier Constraint Reason CRUD Tests - LOOKUP with multilingual
"""

import pytest
import time

from app.core.database import SessionLocal
from app.models.supplier_constraint_reason import SupplierConstraintReason
from app.schemas.supplier_constraint_reason import (
    SupplierConstraintReasonCreate, SupplierConstraintReasonUpdate, SupplierConstraintReasonSearch
)
from app.services.supplier_constraint_reason_service import SupplierConstraintReasonService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def service():
    return SupplierConstraintReasonService()


class TestSupplierConstraintReasonCRUD:
    
    def test_01_create(self, db, service):
        """Create with timestamps"""
        item = service.create(db, SupplierConstraintReasonCreate(
            code=f"SCR-{int(time.time())}",
            name_he=f"סיבת בדיקה {time.time()}",
            name_en=f"Test Reason {time.time()}",
            category="test"
        ), 4)
        assert item.id is not None
        assert item.created_at is not None
        assert item.name_he is not None
        db.delete(item)
        db.commit()
    
    def test_02_get(self, db, service):
        """Get by ID"""
        item = service.create(db, SupplierConstraintReasonCreate(
            code=f"SCR-{int(time.time())}",
            name_he=f"סיבה {time.time()}",
            category="test"
        ), 4)
        fetched = service.get_by_id(db, item.id)
        assert fetched is not None
        db.delete(item)
        db.commit()
    
    def test_03_update_trigger(self, db, service):
        """Update + trigger"""
        item = service.create(db, SupplierConstraintReasonCreate(
            code=f"SCR-{int(time.time())}",
            name_he=f"סיבה {time.time()}",
            category="test"
        ), 4)
        fu = item.updated_at
        time.sleep(2)
        upd = service.update(db, item.id, SupplierConstraintReasonUpdate(description="Updated"), 4)
        assert upd.updated_at > fu, "Trigger should work"
        db.delete(item)
        db.commit()
    
    def test_04_list(self, db, service):
        """List with pagination"""
        item = service.create(db, SupplierConstraintReasonCreate(
            code=f"SCR-{int(time.time())}",
            name_he=f"סיבה {time.time()}",
            category="test"
        ), 4)
        items, total = service.list(db, SupplierConstraintReasonSearch())
        assert total >= 1
        db.delete(item)
        db.commit()
    
    def test_05_by_code(self, db, service):
        """Get by code"""
        code = f"SCR-{int(time.time())}"
        item = service.create(db, SupplierConstraintReasonCreate(
            code=code,
            name_he=f"סיבה {time.time()}",
            category="test"
        ), 4)
        found = service.get_by_code(db, code)
        assert found is not None
        assert found.code == code
        db.delete(item)
        db.commit()
    
    def test_06_soft_delete(self, db, service):
        """Soft delete"""
        item = service.create(db, SupplierConstraintReasonCreate(
            code=f"SCR-{int(time.time())}",
            name_he=f"סיבה {time.time()}",
            category="test"
        ), 4)
        i, t = service.list(db, SupplierConstraintReasonSearch())
        service.soft_delete(db, item.id, 4)
        i2, t2 = service.list(db, SupplierConstraintReasonSearch())
        assert t2 < t
        db.delete(item)
        db.commit()
    
    def test_07_restore(self, db, service):
        """Restore"""
        item = service.create(db, SupplierConstraintReasonCreate(
            code=f"SCR-{int(time.time())}",
            name_he=f"סיבה {time.time()}",
            category="test"
        ), 4)
        service.soft_delete(db, item.id, 4)
        i, t = service.list(db, SupplierConstraintReasonSearch())
        service.restore(db, item.id, 4)
        i2, t2 = service.list(db, SupplierConstraintReasonSearch())
        assert t2 > t
        db.delete(item)
        db.commit()
    
    def test_08_unique_code(self, db, service):
        """UNIQUE code"""
        code = f"UNIQ-{int(time.time())}"
        item = service.create(db, SupplierConstraintReasonCreate(
            code=code,
            name_he=f"סיבה {time.time()}",
            category="test"
        ), 4)
        
        from app.core.exceptions import DuplicateException
        with pytest.raises(DuplicateException):
            service.create(db, SupplierConstraintReasonCreate(
                code=code,
                name_he=f"סיבה אחרת {time.time()}",
                category="test"
            ), 4)
        
        db.delete(item)
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
