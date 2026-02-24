"""
Supplier CRUD Tests - Production Ready Verification
"""

import pytest
import time

from app.core.database import SessionLocal
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierSearch
from app.services.supplier_service import SupplierService


@pytest.fixture
def db():
    """Database session fixture"""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def supplier_service():
    """Supplier service fixture"""
    return SupplierService()


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return 4


class TestSupplierCRUD:
    """Supplier CRUD test suite"""
    
    def test_01_create_supplier(self, db, supplier_service, test_user_id):
        """Test supplier creation with auto-populated timestamps"""
        # Arrange
        data = SupplierCreate(
            name=f"Test Supplier {int(time.time())}",
            code=f"TST-{int(time.time())}",
            supplier_type="equipment"
        )
        
        # Act
        supplier = supplier_service.create(db, data, test_user_id)
        
        # Assert
        assert supplier.id is not None
        assert supplier.name is not None
        assert supplier.created_at is not None
        assert supplier.updated_at is not None
        assert supplier.version is not None
        
        # Cleanup
        db.delete(supplier)
        db.commit()
    
    def test_02_get_by_id(self, db, supplier_service, test_user_id):
        """Test getting supplier by ID"""
        # Arrange
        supplier = supplier_service.create(
            db,
            SupplierCreate(name=f"Test Get {int(time.time())}", code=f"GET-{int(time.time())}"),
            test_user_id
        )
        
        # Act
        fetched = supplier_service.get_by_id(db, supplier.id)
        
        # Assert
        assert fetched is not None
        assert fetched.id == supplier.id
        
        # Cleanup
        db.delete(supplier)
        db.commit()
    
    def test_03_update_with_trigger(self, db, supplier_service, test_user_id):
        """Test update and verify DB trigger updates updated_at"""
        # Arrange
        supplier = supplier_service.create(
            db,
            SupplierCreate(name=f"Test Update {int(time.time())}", code=f"UPD-{int(time.time())}"),
            test_user_id
        )
        original_updated_at = supplier.updated_at
        
        # Act - wait and update
        time.sleep(2)
        updated = supplier_service.update(
            db,
            supplier.id,
            SupplierUpdate(name=f"Test Update Modified {int(time.time())}"),
            test_user_id
        )
        
        # Assert
        assert updated.updated_at > original_updated_at, "updated_at should be changed by DB trigger"
        
        # Cleanup
        db.delete(supplier)
        db.commit()
    
    def test_04_list_with_pagination(self, db, supplier_service, test_user_id):
        """Test listing suppliers with pagination"""
        # Arrange
        s1 = supplier_service.create(db, SupplierCreate(name=f"List 1 {int(time.time())}", code=f"L1-{int(time.time())}"), test_user_id)
        s2 = supplier_service.create(db, SupplierCreate(name=f"List 2 {int(time.time())}", code=f"L2-{int(time.time())}"), test_user_id)
        
        # Act
        items, total = supplier_service.list(db, SupplierSearch(page=1, page_size=100))
        
        # Assert
        assert total >= 2
        assert any(s.id == s1.id for s in items)
        assert any(s.id == s2.id for s in items)
        
        # Cleanup
        db.delete(s1)
        db.delete(s2)
        db.commit()
    
    def test_05_soft_delete_filters_from_list(self, db, supplier_service, test_user_id):
        """Test soft delete filters from list"""
        # Arrange
        supplier = supplier_service.create(
            db,
            SupplierCreate(name=f"Test Delete {int(time.time())}", code=f"DEL-{int(time.time())}"),
            test_user_id
        )
        items_before, total_before = supplier_service.list(db, SupplierSearch())
        
        # Act
        deleted = supplier_service.soft_delete(db, supplier.id, test_user_id)
        
        # Assert
        assert deleted.deleted_at is not None
        items_after, total_after = supplier_service.list(db, SupplierSearch())
        assert total_after < total_before
        
        # Cleanup
        db.delete(supplier)
        db.commit()
    
    def test_06_restore_brings_back_to_list(self, db, supplier_service, test_user_id):
        """Test restore brings back to list"""
        # Arrange
        supplier = supplier_service.create(
            db,
            SupplierCreate(name=f"Test Restore {int(time.time())}", code=f"RST-{int(time.time())}"),
            test_user_id
        )
        supplier_service.soft_delete(db, supplier.id, test_user_id)
        items_deleted, total_deleted = supplier_service.list(db, SupplierSearch())
        
        # Act
        restored = supplier_service.restore(db, supplier.id, test_user_id)
        
        # Assert
        assert restored.deleted_at is None
        items_restored, total_restored = supplier_service.list(db, SupplierSearch())
        assert total_restored > total_deleted
        
        # Cleanup
        db.delete(supplier)
        db.commit()
    
    def test_07_unique_name_constraint(self, db, supplier_service, test_user_id):
        """Test duplicate name raises DuplicateException"""
        # Arrange
        name = f"Unique Test {int(time.time())}"
        s1 = supplier_service.create(db, SupplierCreate(name=name, code=f"UNQ1-{int(time.time())}"), test_user_id)
        
        # Act & Assert
        from app.core.exceptions import DuplicateException
        with pytest.raises(DuplicateException):
            supplier_service.create(db, SupplierCreate(name=name, code=f"UNQ2-{int(time.time())}"), test_user_id)
        
        # Cleanup
        db.delete(s1)
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
