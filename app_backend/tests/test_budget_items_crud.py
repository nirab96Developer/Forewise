"""
BudgetItem CRUD Tests
"""

import pytest
import time
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.budget_item import BudgetItem
from app.models.budget import Budget
from app.schemas.budget_item import BudgetItemCreate, BudgetItemUpdate, BudgetItemSearch
from app.services.budget_item_service import BudgetItemService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def budget_item_service():
    return BudgetItemService()


@pytest.fixture
def test_budget(db):
    """Create test budget"""
    budget = Budget(name="Test Budget for Items", code=f"TEST-{int(time.time())}", budget_type="CAPITAL", total_amount=Decimal('500000'), status="ACTIVE")
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


class TestBudgetItemCRUD:
    
    def test_01_create(self, db, budget_item_service, test_budget):
        """Create with timestamps"""
        item = budget_item_service.create(db, BudgetItemCreate(
            budget_id=test_budget.id,
            item_name="Test Item",
            item_type="EXPENSE",
            planned_amount=Decimal('10000')
        ), 4)
        assert item.id is not None
        assert item.created_at is not None
        db.delete(item)
        db.delete(test_budget)
        db.commit()
    
    def test_02_get(self, db, budget_item_service, test_budget):
        """Get by ID"""
        item = budget_item_service.create(db, BudgetItemCreate(budget_id=test_budget.id, item_name="Test", item_type="EXPENSE", planned_amount=Decimal('10000')), 4)
        fetched = budget_item_service.get_by_id(db, item.id)
        assert fetched is not None
        db.delete(item)
        db.delete(test_budget)
        db.commit()
    
    def test_03_update_trigger(self, db, budget_item_service, test_budget):
        """Update + trigger"""
        item = budget_item_service.create(db, BudgetItemCreate(budget_id=test_budget.id, item_name="Test", item_type="EXPENSE", planned_amount=Decimal('10000')), 4)
        fu = item.updated_at
        time.sleep(2)
        upd = budget_item_service.update(db, item.id, BudgetItemUpdate(item_name="Updated"), 4)
        assert upd.updated_at > fu, "Trigger should work"
        db.delete(item)
        db.delete(test_budget)
        db.commit()
    
    def test_04_list(self, db, budget_item_service, test_budget):
        """List"""
        item = budget_item_service.create(db, BudgetItemCreate(budget_id=test_budget.id, item_name="Test", item_type="EXPENSE", planned_amount=Decimal('10000')), 4)
        items, total = budget_item_service.list(db, BudgetItemSearch())
        assert total >= 1
        db.delete(item)
        db.delete(test_budget)
        db.commit()
    
    def test_05_list_by_budget(self, db, budget_item_service, test_budget):
        """List by budget_id"""
        item = budget_item_service.create(db, BudgetItemCreate(budget_id=test_budget.id, item_name="Test", item_type="EXPENSE", planned_amount=Decimal('10000')), 4)
        items, total = budget_item_service.list(db, BudgetItemSearch(budget_id=test_budget.id))
        assert any(i.id == item.id for i in items)
        db.delete(item)
        db.delete(test_budget)
        db.commit()
    
    def test_06_soft_delete(self, db, budget_item_service, test_budget):
        """Soft delete"""
        item = budget_item_service.create(db, BudgetItemCreate(budget_id=test_budget.id, item_name="Test", item_type="EXPENSE", planned_amount=Decimal('10000')), 4)
        i, t = budget_item_service.list(db, BudgetItemSearch())
        deleted = budget_item_service.soft_delete(db, item.id, 4)
        i2, t2 = budget_item_service.list(db, BudgetItemSearch())
        assert t2 < t
        db.delete(item)
        db.delete(test_budget)
        db.commit()
    
    def test_07_restore(self, db, budget_item_service, test_budget):
        """Restore"""
        item = budget_item_service.create(db, BudgetItemCreate(budget_id=test_budget.id, item_name="Test", item_type="EXPENSE", planned_amount=Decimal('10000')), 4)
        budget_item_service.soft_delete(db, item.id, 4)
        i, t = budget_item_service.list(db, BudgetItemSearch())
        restored = budget_item_service.restore(db, item.id, 4)
        i2, t2 = budget_item_service.list(db, BudgetItemSearch())
        assert t2 > t
        db.delete(item)
        db.delete(test_budget)
        db.commit()
    
    def test_08_fk_validation(self, db, budget_item_service):
        """FK validation"""
        from app.core.exceptions import ValidationException
        with pytest.raises(ValidationException):
            budget_item_service.create(db, BudgetItemCreate(budget_id=999999, item_name="Test", item_type="EXPENSE", planned_amount=Decimal('10000')), 4)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
