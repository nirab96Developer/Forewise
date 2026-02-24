"""
Integration Test: Budget → Budget Items Flow
Verifies hierarchy and relationships work together
"""

import pytest
import time
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.budget import Budget
from app.schemas.budget import BudgetCreate
from app.schemas.budget_item import BudgetItemCreate, BudgetItemUpdate, BudgetItemSearch
from app.services.budget_service import BudgetService
from app.services.budget_item_service import BudgetItemService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


class TestBudgetItemsIntegration:
    """Budget → Budget Items integration flow"""
    
    def test_01_create_budget(self, db):
        """Create budget"""
        budget_service = BudgetService()
        budget = budget_service.create(db, BudgetCreate(
            name=f"Integration Budget {time.time()}",
            code=f"INT-{int(time.time())}",
            budget_type="CAPITAL",
            total_amount=Decimal('500000')
        ), 4)
        
        assert budget.id is not None
        assert budget.created_at is not None
        
        # Cleanup
        db.delete(budget)
        db.commit()
    
    def test_02_create_items_under_budget(self, db):
        """Create 2 items under same budget"""
        budget_service = BudgetService()
        item_service = BudgetItemService()
        
        # Create budget
        budget = budget_service.create(db, BudgetCreate(
            name="Test Budget",
            code=f"TB-{int(time.time())}",
            budget_type="CAPITAL",
            total_amount=Decimal('500000')
        ), 4)
        
        # Create 2 items
        item1 = item_service.create(db, BudgetItemCreate(
            budget_id=budget.id,
            item_name="Item 1",
            item_type="EXPENSE",
            planned_amount=Decimal('100000')
        ), 4)
        
        item2 = item_service.create(db, BudgetItemCreate(
            budget_id=budget.id,
            item_name="Item 2",
            item_type="EXPENSE",
            planned_amount=Decimal('150000')
        ), 4)
        
        assert item1.budget_id == budget.id
        assert item2.budget_id == budget.id
        
        # Cleanup
        db.delete(item1)
        db.delete(item2)
        db.delete(budget)
        db.commit()
    
    def test_03_list_items_by_budget(self, db):
        """List items filtered by budget_id"""
        budget_service = BudgetService()
        item_service = BudgetItemService()
        
        budget = budget_service.create(db, BudgetCreate(
            name="Test",
            code=f"TB-{int(time.time())}",
            budget_type="CAPITAL",
            total_amount=Decimal('500000')
        ), 4)
        
        item1 = item_service.create(db, BudgetItemCreate(
            budget_id=budget.id,
            item_name="Item 1",
            item_type="EXPENSE",
            planned_amount=Decimal('100000')
        ), 4)
        
        item2 = item_service.create(db, BudgetItemCreate(
            budget_id=budget.id,
            item_name="Item 2",
            item_type="EXPENSE",
            planned_amount=Decimal('150000')
        ), 4)
        
        # List items by budget
        items, total = item_service.list(db, BudgetItemSearch(budget_id=budget.id))
        
        assert total == 2
        assert all(i.budget_id == budget.id for i in items)
        
        # Cleanup
        db.delete(item1)
        db.delete(item2)
        db.delete(budget)
        db.commit()
    
    def test_04_update_item_trigger(self, db):
        """Update item + verify trigger"""
        budget_service = BudgetService()
        item_service = BudgetItemService()
        
        budget = budget_service.create(db, BudgetCreate(
            name="Test",
            code=f"TB-{int(time.time())}",
            budget_type="CAPITAL",
            total_amount=Decimal('500000')
        ), 4)
        
        item = item_service.create(db, BudgetItemCreate(
            budget_id=budget.id,
            item_name="Item",
            item_type="EXPENSE",
            planned_amount=Decimal('100000')
        ), 4)
        
        fu = item.updated_at
        time.sleep(2)
        
        updated = item_service.update(db, item.id, BudgetItemUpdate(item_name="Updated Item"), 4)
        
        assert updated.updated_at > fu, "Trigger should work"
        
        # Cleanup
        db.delete(item)
        db.delete(budget)
        db.commit()
    
    def test_05_calculate_totals(self, db):
        """Calculate totals from items"""
        budget_service = BudgetService()
        item_service = BudgetItemService()
        
        budget = budget_service.create(db, BudgetCreate(
            name="Test",
            code=f"TB-{int(time.time())}",
            budget_type="CAPITAL",
            total_amount=Decimal('500000')
        ), 4)
        
        item1 = item_service.create(db, BudgetItemCreate(
            budget_id=budget.id,
            item_name="Item 1",
            item_type="EXPENSE",
            planned_amount=Decimal('100000')
        ), 4)
        
        item2 = item_service.create(db, BudgetItemCreate(
            budget_id=budget.id,
            item_name="Item 2",
            item_type="EXPENSE",
            planned_amount=Decimal('150000')
        ), 4)
        
        # Calculate total
        items, _ = item_service.list(db, BudgetItemSearch(budget_id=budget.id))
        total_planned = sum(i.planned_amount for i in items)
        
        assert total_planned == Decimal('250000')
        
        # Cleanup
        db.delete(item1)
        db.delete(item2)
        db.delete(budget)
        db.commit()
    
    def test_06_soft_delete_item(self, db):
        """Soft delete item doesn't break budget"""
        budget_service = BudgetService()
        item_service = BudgetItemService()
        
        budget = budget_service.create(db, BudgetCreate(
            name="Test",
            code=f"TB-{int(time.time())}",
            budget_type="CAPITAL",
            total_amount=Decimal('500000')
        ), 4)
        
        item = item_service.create(db, BudgetItemCreate(
            budget_id=budget.id,
            item_name="Item",
            item_type="EXPENSE",
            planned_amount=Decimal('100000')
        ), 4)
        
        # Soft delete item
        item_service.soft_delete(db, item.id, 4)
        
        # Budget should still exist
        fetched_budget = budget_service.get_by_id(db, budget.id)
        assert fetched_budget is not None
        
        # Items list should be empty (soft deleted)
        items, total = item_service.list(db, BudgetItemSearch(budget_id=budget.id))
        assert total == 0
        
        # Cleanup
        db.delete(item)
        db.delete(budget)
        db.commit()
    
    def test_07_restore_item(self, db):
        """Restore soft-deleted item"""
        budget_service = BudgetService()
        item_service = BudgetItemService()
        
        budget = budget_service.create(db, BudgetCreate(
            name="Test",
            code=f"TB-{int(time.time())}",
            budget_type="CAPITAL",
            total_amount=Decimal('500000')
        ), 4)
        
        item = item_service.create(db, BudgetItemCreate(
            budget_id=budget.id,
            item_name="Item",
            item_type="EXPENSE",
            planned_amount=Decimal('100000')
        ), 4)
        
        # Soft delete
        item_service.soft_delete(db, item.id, 4)
        items_deleted, total_deleted = item_service.list(db, BudgetItemSearch(budget_id=budget.id))
        
        # Restore
        item_service.restore(db, item.id, 4)
        items_restored, total_restored = item_service.list(db, BudgetItemSearch(budget_id=budget.id))
        
        assert total_restored > total_deleted
        
        # Cleanup
        db.delete(item)
        db.delete(budget)
        db.commit()
    
    def test_08_fk_validation_invalid_budget(self, db):
        """FK validation: invalid budget_id"""
        item_service = BudgetItemService()
        
        from app.core.exceptions import ValidationException
        with pytest.raises(ValidationException):
            item_service.create(db, BudgetItemCreate(
                budget_id=999999,
                item_name="Bad Item",
                item_type="EXPENSE",
                planned_amount=Decimal('100000')
            ), 4)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
