"""
Budget CRUD Tests
"""

import pytest
import time
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetSearch
from app.services.budget_service import BudgetService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def budget_service():
    return BudgetService()


@pytest.fixture
def test_user_id():
    return 4


class TestBudgetCRUD:
    
    def test_01_create(self, db, budget_service, test_user_id):
        """Create with timestamps"""
        b = budget_service.create(db, BudgetCreate(
            name=f"Test Budget {time.time()}",
            code=f"TB-{int(time.time())}",
            budget_type="CAPITAL",
            total_amount=Decimal('100000')
        ), test_user_id)
        assert b.id is not None
        assert b.created_at is not None
        db.delete(b)
        db.commit()
    
    def test_02_get(self, db, budget_service, test_user_id):
        """Get by ID"""
        b = budget_service.create(db, BudgetCreate(name="Test", code=f"G-{int(time.time())}", budget_type="CAPITAL", total_amount=Decimal('100000')), test_user_id)
        fetched = budget_service.get_by_id(db, b.id)
        assert fetched is not None
        db.delete(b)
        db.commit()
    
    def test_03_update_trigger(self, db, budget_service, test_user_id):
        """Update + trigger"""
        b = budget_service.create(db, BudgetCreate(name="Test", code=f"U-{int(time.time())}", budget_type="CAPITAL", total_amount=Decimal('100000')), test_user_id)
        fu = b.updated_at
        time.sleep(2)
        upd = budget_service.update(db, b.id, BudgetUpdate(name="Updated"), test_user_id)
        assert upd.updated_at > fu, "Trigger should work"
        db.delete(b)
        db.commit()
    
    def test_04_list(self, db, budget_service, test_user_id):
        """List"""
        b1 = budget_service.create(db, BudgetCreate(name="L1", code=f"L1-{int(time.time())}", budget_type="CAPITAL", total_amount=Decimal('100000')), test_user_id)
        items, total = budget_service.list(db, BudgetSearch())
        assert total >= 1
        db.delete(b1)
        db.commit()
    
    def test_05_by_code(self, db, budget_service, test_user_id):
        """Get by code"""
        code = f"BC-{int(time.time())}"
        b = budget_service.create(db, BudgetCreate(name="Test", code=code, budget_type="CAPITAL", total_amount=Decimal('100000')), test_user_id)
        found = budget_service.get_by_code(db, code)
        assert found is not None
        db.delete(b)
        db.commit()
    
    def test_06_soft_delete(self, db, budget_service, test_user_id):
        """Soft delete"""
        b = budget_service.create(db, BudgetCreate(name="Test", code=f"D-{int(time.time())}", budget_type="CAPITAL", total_amount=Decimal('100000')), test_user_id)
        i, t = budget_service.list(db, BudgetSearch())
        deleted = budget_service.soft_delete(db, b.id, test_user_id)
        i2, t2 = budget_service.list(db, BudgetSearch())
        assert t2 < t
        db.delete(b)
        db.commit()
    
    def test_07_restore(self, db, budget_service, test_user_id):
        """Restore"""
        b = budget_service.create(db, BudgetCreate(name="Test", code=f"R-{int(time.time())}", budget_type="CAPITAL", total_amount=Decimal('100000')), test_user_id)
        budget_service.soft_delete(db, b.id, test_user_id)
        i, t = budget_service.list(db, BudgetSearch())
        restored = budget_service.restore(db, b.id, test_user_id)
        i2, t2 = budget_service.list(db, BudgetSearch())
        assert t2 > t
        db.delete(b)
        db.commit()
    
    def test_08_self_ref(self, db, budget_service, test_user_id):
        """Self-reference parent"""
        parent = budget_service.create(db, BudgetCreate(name="Parent", code=f"P-{int(time.time())}", budget_type="CAPITAL", total_amount=Decimal('500000')), test_user_id)
        child = budget_service.create(db, BudgetCreate(name="Child", code=f"C-{int(time.time())}", budget_type="CAPITAL", total_amount=Decimal('100000'), parent_budget_id=parent.id), test_user_id)
        assert child.parent_budget_id == parent.id
        db.delete(child)
        db.delete(parent)
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
