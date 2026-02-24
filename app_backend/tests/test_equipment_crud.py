"""
Equipment CRUD Tests - Production Ready Verification
Tests all CRUD operations to ensure Equipment module works correctly
"""

import pytest
import time
from datetime import datetime

from app.core.database import SessionLocal
from app.models.equipment import Equipment
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate, EquipmentSearch
from app.services.equipment_service import EquipmentService


@pytest.fixture
def db():
    """Database session fixture"""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def equipment_service():
    """Equipment service fixture"""
    return EquipmentService()


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return 4  # Admin user


class TestEquipmentCRUD:
    """Equipment CRUD test suite"""
    
    def test_01_create_equipment(self, db, equipment_service, test_user_id):
        """Test equipment creation with auto-populated timestamps"""
        # Arrange
        data = EquipmentCreate(
            name="Test Bulldozer",
            code=f"TEST-{int(time.time())}",
            status="available"
        )
        
        # Act
        equipment = equipment_service.create(db, data, test_user_id)
        
        # Assert
        assert equipment.id is not None
        assert equipment.name == "Test Bulldozer"
        assert equipment.created_at is not None, "created_at should be auto-populated"
        assert equipment.updated_at is not None, "updated_at should be auto-populated"
        assert equipment.is_active == True
        assert equipment.deleted_at is None
        
        # Cleanup
        db.delete(equipment)
        db.commit()
    
    def test_02_get_by_id(self, db, equipment_service, test_user_id):
        """Test getting equipment by ID"""
        # Arrange - create equipment
        equipment = equipment_service.create(
            db,
            EquipmentCreate(name="Test Get", code=f"GET-{int(time.time())}", status="available"),
            test_user_id
        )
        
        # Act
        fetched = equipment_service.get_by_id(db, equipment.id)
        
        # Assert
        assert fetched is not None
        assert fetched.id == equipment.id
        assert fetched.name == "Test Get"
        
        # Cleanup
        db.delete(equipment)
        db.commit()
    
    def test_03_update_with_trigger(self, db, equipment_service, test_user_id):
        """Test update and verify DB trigger updates updated_at"""
        # Arrange - create equipment
        equipment = equipment_service.create(
            db,
            EquipmentCreate(name="Test Update", code=f"UPD-{int(time.time())}", status="available"),
            test_user_id
        )
        original_updated_at = equipment.updated_at
        
        # Act - wait and update
        time.sleep(2)  # Wait so trigger can set different time
        update_data = EquipmentUpdate(name="Test Update - MODIFIED")
        updated = equipment_service.update(db, equipment.id, update_data, test_user_id)
        
        # Assert
        assert updated.name == "Test Update - MODIFIED"
        assert updated.updated_at > original_updated_at, "updated_at should be changed by DB trigger"
        
        # Cleanup
        db.delete(equipment)
        db.commit()
    
    def test_04_list_with_pagination(self, db, equipment_service, test_user_id):
        """Test listing equipment with pagination"""
        # Arrange - create test equipment
        eq1 = equipment_service.create(db, EquipmentCreate(name="List Test 1", code=f"LST1-{int(time.time())}", status="available"), test_user_id)
        eq2 = equipment_service.create(db, EquipmentCreate(name="List Test 2", code=f"LST2-{int(time.time())}", status="available"), test_user_id)
        
        # Act
        search = EquipmentSearch(page=1, page_size=100)
        items, total = equipment_service.list(db, search)
        
        # Assert
        assert total >= 2
        assert len(items) <= 100
        assert any(e.id == eq1.id for e in items)
        assert any(e.id == eq2.id for e in items)
        
        # Cleanup
        db.delete(eq1)
        db.delete(eq2)
        db.commit()
    
    def test_05_soft_delete_filters_from_list(self, db, equipment_service, test_user_id):
        """Test soft delete sets deleted_at and filters from list"""
        # Arrange - create equipment
        equipment = equipment_service.create(
            db,
            EquipmentCreate(name="Test Delete", code=f"DEL-{int(time.time())}", status="available"),
            test_user_id
        )
        
        # Get initial count
        items_before, total_before = equipment_service.list(db, EquipmentSearch())
        
        # Act - soft delete
        deleted = equipment_service.soft_delete(db, equipment.id, test_user_id)
        
        # Assert
        assert deleted.deleted_at is not None, "deleted_at should be set"
        assert deleted.is_active == False, "is_active should be False"
        
        # Verify not in list
        items_after, total_after = equipment_service.list(db, EquipmentSearch())
        assert total_after < total_before, "Equipment should not appear in list after soft delete"
        assert not any(e.id == equipment.id for e in items_after)
        
        # Cleanup
        db.delete(equipment)
        db.commit()
    
    def test_06_restore_brings_back_to_list(self, db, equipment_service, test_user_id):
        """Test restore clears deleted_at and brings back to list"""
        # Arrange - create and soft delete
        equipment = equipment_service.create(
            db,
            EquipmentCreate(name="Test Restore", code=f"RST-{int(time.time())}", status="available"),
            test_user_id
        )
        equipment_service.soft_delete(db, equipment.id, test_user_id)
        
        # Get count after delete
        items_deleted, total_deleted = equipment_service.list(db, EquipmentSearch())
        
        # Act - restore
        restored = equipment_service.restore(db, equipment.id, test_user_id)
        
        # Assert
        assert restored.deleted_at is None, "deleted_at should be cleared"
        assert restored.is_active == True, "is_active should be True"
        
        # Verify back in list
        items_restored, total_restored = equipment_service.list(db, EquipmentSearch())
        assert total_restored > total_deleted, "Equipment should be back in list after restore"
        assert any(e.id == equipment.id for e in items_restored)
        
        # Cleanup
        db.delete(equipment)
        db.commit()


class TestEquipmentValidations:
    """Equipment validation test suite"""
    
    def test_unique_code_constraint(self, db, equipment_service, test_user_id):
        """Test duplicate code raises DuplicateException"""
        # Arrange
        code = f"UNQ-{int(time.time())}"
        eq1 = equipment_service.create(
            db,
            EquipmentCreate(name="First", code=code, status="available"),
            test_user_id
        )
        
        # Act & Assert
        from app.core.exceptions import DuplicateException
        with pytest.raises(DuplicateException):
            equipment_service.create(
                db,
                EquipmentCreate(name="Second", code=code, status="available"),
                test_user_id
            )
        
        # Cleanup
        db.delete(eq1)
        db.commit()


if __name__ == "__main__":
    # Can run directly for manual testing
    pytest.main([__file__, "-v"])
