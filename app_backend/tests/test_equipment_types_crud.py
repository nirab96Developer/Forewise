"""
Equipment Type CRUD Tests - LOOKUP
"""

import pytest
import time
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.equipment_type import EquipmentType
from app.schemas.equipment_type import EquipmentTypeCreate, EquipmentTypeUpdate, EquipmentTypeSearch
from app.services.equipment_type_service import EquipmentTypeService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def eq_type_service():
    return EquipmentTypeService()


class TestEquipmentTypeCRUD:
    
    def test_01_create(self, db, eq_type_service):
        """Create with timestamps"""
        item = eq_type_service.create(db, EquipmentTypeCreate(
            code=f"EQTYPE-{int(time.time())}",
            name=f"Test Equipment Type {time.time()}",
            default_hourly_rate=Decimal("100.00"),
            default_storage_hourly_rate=Decimal("25.00")
        ), 4)
        assert item.id is not None
        assert item.created_at is not None
        db.delete(item)
        db.commit()
    
    def test_02_get(self, db, eq_type_service):
        """Get by ID"""
        item = eq_type_service.create(db, EquipmentTypeCreate(
            code=f"EQTYPE-{int(time.time())}",
            name=f"Test {time.time()}",
            default_hourly_rate=Decimal("100.00"),
            default_storage_hourly_rate=Decimal("25.00")
        ), 4)
        fetched = eq_type_service.get_by_id(db, item.id)
        assert fetched is not None
        db.delete(item)
        db.commit()
    
    def test_03_update_trigger(self, db, eq_type_service):
        """Update + trigger"""
        item = eq_type_service.create(db, EquipmentTypeCreate(
            code=f"EQTYPE-{int(time.time())}",
            name=f"Test {time.time()}",
            default_hourly_rate=Decimal("100.00"),
            default_storage_hourly_rate=Decimal("25.00")
        ), 4)
        fu = item.updated_at
        time.sleep(2)
        upd = eq_type_service.update(db, item.id, EquipmentTypeUpdate(description="Updated"), 4)
        assert upd.updated_at > fu, "Trigger should work"
        db.delete(item)
        db.commit()
    
    def test_04_list(self, db, eq_type_service):
        """List with pagination"""
        item = eq_type_service.create(db, EquipmentTypeCreate(
            code=f"EQTYPE-{int(time.time())}",
            name=f"Test {time.time()}",
            default_hourly_rate=Decimal("100.00"),
            default_storage_hourly_rate=Decimal("25.00")
        ), 4)
        items, total = eq_type_service.list(db, EquipmentTypeSearch())
        assert total >= 1
        db.delete(item)
        db.commit()
    
    def test_05_by_code(self, db, eq_type_service):
        """Get by code"""
        code = f"EQTYPE-{int(time.time())}"
        item = eq_type_service.create(db, EquipmentTypeCreate(
            code=code,
            name=f"Test {time.time()}",
            default_hourly_rate=Decimal("100.00"),
            default_storage_hourly_rate=Decimal("25.00")
        ), 4)
        found = eq_type_service.get_by_code(db, code)
        assert found is not None
        assert found.code == code
        db.delete(item)
        db.commit()
    
    def test_06_deactivate(self, db, eq_type_service):
        """Deactivate"""
        item = eq_type_service.create(db, EquipmentTypeCreate(
            code=f"EQTYPE-{int(time.time())}",
            name=f"Test {time.time()}",
            default_hourly_rate=Decimal("100.00"),
            default_storage_hourly_rate=Decimal("25.00")
        ), 4)
        assert item.is_active == True
        deactivated = eq_type_service.deactivate(db, item.id, 4)
        assert deactivated.is_active == False
        db.delete(item)
        db.commit()
    
    def test_07_activate(self, db, eq_type_service):
        """Activate"""
        item = eq_type_service.create(db, EquipmentTypeCreate(
            code=f"EQTYPE-{int(time.time())}",
            name=f"Test {time.time()}",
            default_hourly_rate=Decimal("100.00"),
            default_storage_hourly_rate=Decimal("25.00")
        ), 4)
        eq_type_service.deactivate(db, item.id, 4)
        activated = eq_type_service.activate(db, item.id, 4)
        assert activated.is_active == True
        db.delete(item)
        db.commit()
    
    def test_08_unique_code(self, db, eq_type_service):
        """UNIQUE code"""
        code = f"UNIQ-{int(time.time())}"
        item = eq_type_service.create(db, EquipmentTypeCreate(
            code=code,
            name=f"Test {time.time()}",
            default_hourly_rate=Decimal("100.00"),
            default_storage_hourly_rate=Decimal("25.00")
        ), 4)
        
        from app.core.exceptions import DuplicateException
        with pytest.raises(DuplicateException):
            eq_type_service.create(db, EquipmentTypeCreate(
                code=code,
                name=f"Another {time.time()}",
                default_hourly_rate=Decimal("200.00"),
                default_storage_hourly_rate=Decimal("50.00")
            ), 4)
        
        db.delete(item)
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
