"""
Equipment Category CRUD Tests - CORE with self-ref
"""

import pytest
import time

from app.core.database import SessionLocal
from app.models.equipment_category import EquipmentCategory
from app.schemas.equipment_category import (
    EquipmentCategoryCreate, EquipmentCategoryUpdate, EquipmentCategorySearch
)
from app.services.equipment_category_service import EquipmentCategoryService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def service():
    return EquipmentCategoryService()


class TestEquipmentCategoryCRUD:
    
    def test_01_create(self, db, service):
        """Create with timestamps"""
        item = service.create(db, EquipmentCategoryCreate(
            code=f"EQCAT-{int(time.time())}",
            name=f"Test Category {time.time()}"
        ), 4)
        assert item.id is not None
        assert item.created_at is not None
        assert item.version == 1
        db.delete(item)
        db.commit()
    
    def test_02_get(self, db, service):
        """Get by ID"""
        item = service.create(db, EquipmentCategoryCreate(
            code=f"EQCAT-{int(time.time())}",
            name=f"Test {time.time()}"
        ), 4)
        fetched = service.get_by_id(db, item.id)
        assert fetched is not None
        db.delete(item)
        db.commit()
    
    def test_03_update_trigger(self, db, service):
        """Update + trigger"""
        item = service.create(db, EquipmentCategoryCreate(
            code=f"EQCAT-{int(time.time())}",
            name=f"Test {time.time()}"
        ), 4)
        fu = item.updated_at
        time.sleep(2)
        upd = service.update(db, item.id, EquipmentCategoryUpdate(description="Updated"), 4)
        assert upd.updated_at > fu, "Trigger should work"
        assert upd.version == 2
        db.delete(item)
        db.commit()
    
    def test_04_list(self, db, service):
        """List with pagination"""
        item = service.create(db, EquipmentCategoryCreate(
            code=f"EQCAT-{int(time.time())}",
            name=f"Test {time.time()}"
        ), 4)
        items, total = service.list(db, EquipmentCategorySearch())
        assert total >= 1
        db.delete(item)
        db.commit()
    
    def test_05_children(self, db, service):
        """Self-ref: parent -> children"""
        parent = service.create(db, EquipmentCategoryCreate(
            code=f"PARENT-{int(time.time())}",
            name=f"Parent {time.time()}"
        ), 4)
        
        child = service.create(db, EquipmentCategoryCreate(
            code=f"CHILD-{int(time.time())}",
            name=f"Child {time.time()}",
            parent_category_id=parent.id
        ), 4)
        
        children = service.get_children(db, parent.id)
        assert len(children) >= 1
        assert any(c.id == child.id for c in children)
        
        db.delete(child)
        db.delete(parent)
        db.commit()
    
    def test_06_soft_delete(self, db, service):
        """Soft delete"""
        item = service.create(db, EquipmentCategoryCreate(
            code=f"EQCAT-{int(time.time())}",
            name=f"Test {time.time()}"
        ), 4)
        i, t = service.list(db, EquipmentCategorySearch())
        service.soft_delete(db, item.id, 4)
        i2, t2 = service.list(db, EquipmentCategorySearch())
        assert t2 < t
        db.delete(item)
        db.commit()
    
    def test_07_restore(self, db, service):
        """Restore"""
        item = service.create(db, EquipmentCategoryCreate(
            code=f"EQCAT-{int(time.time())}",
            name=f"Test {time.time()}"
        ), 4)
        service.soft_delete(db, item.id, 4)
        i, t = service.list(db, EquipmentCategorySearch())
        service.restore(db, item.id, 4)
        i2, t2 = service.list(db, EquipmentCategorySearch())
        assert t2 > t
        db.delete(item)
        db.commit()
    
    def test_08_validation(self, db, service):
        """UNIQUE code/name + self-ref validation"""
        code = f"UNIQ-{int(time.time())}"
        name = f"Unique Name {time.time()}"
        item = service.create(db, EquipmentCategoryCreate(
            code=code,
            name=name
        ), 4)
        
        from app.core.exceptions import DuplicateException, ValidationException
        
        # Test UNIQUE code
        with pytest.raises(DuplicateException):
            service.create(db, EquipmentCategoryCreate(
                code=code,
                name=f"Another {time.time()}"
            ), 4)
        
        # Test UNIQUE name
        with pytest.raises(DuplicateException):
            service.create(db, EquipmentCategoryCreate(
                code=f"OTHER-{int(time.time())}",
                name=name
            ), 4)
        
        # Test self-referential validation (can't be own parent)
        with pytest.raises(ValidationException):
            service.update(db, item.id, EquipmentCategoryUpdate(
                parent_category_id=item.id
            ), 4)
        
        db.delete(item)
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
