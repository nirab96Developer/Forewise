"""
Area CRUD Tests
"""

import pytest
import time

from app.core.database import SessionLocal
from app.models.area import Area
from app.models.region import Region
from app.schemas.area import AreaCreate, AreaUpdate, AreaSearch
from app.services.area_service import AreaService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def area_service():
    return AreaService()


@pytest.fixture
def test_region(db):
    """Create test region for FK"""
    region = Region(name=f"Test Region {time.time()}", code=f"RGN-{int(time.time())}")
    db.add(region)
    db.commit()
    db.refresh(region)
    yield region
    db.query(Area).filter(Area.region_id == region.id).delete()
    db.delete(region)
    db.commit()


class TestAreaCRUD:
    
    def test_01_create(self, db, area_service, test_region):
        """Create with timestamps"""
        area = area_service.create(db, AreaCreate(
            name=f"Test Area {time.time()}",
            code=f"AREA-{int(time.time())}",
            region_id=test_region.id
        ), 4)
        assert area.id is not None
        assert area.created_at is not None
        assert area.updated_at is not None
        assert area.region_id == test_region.id
        db.delete(area)
        db.commit()
    
    def test_02_get(self, db, area_service, test_region):
        """Get by ID"""
        area = area_service.create(db, AreaCreate(
            name=f"Test {time.time()}",
            code=f"AR-{time.time_ns()}",
            region_id=test_region.id
        ), 4)
        fetched = area_service.get_by_id(db, area.id)
        assert fetched is not None
        db.delete(area)
        db.commit()
    
    def test_03_update_trigger(self, db, area_service, test_region):
        """Update + trigger"""
        area = area_service.create(db, AreaCreate(
            name=f"Test {time.time()}",
            code=f"AR-{time.time_ns()}",
            region_id=test_region.id
        ), 4)
        upd = area_service.update(db, area.id, AreaUpdate(description="Updated"), 4)
        assert upd.description == "Updated"
        if area.updated_at:
            assert upd.updated_at >= area.updated_at
        db.delete(area)
        db.commit()
    
    def test_04_list(self, db, area_service, test_region):
        """List with pagination"""
        area = area_service.create(db, AreaCreate(
            name=f"Test {time.time()}",
            code=f"AR-{time.time_ns()}",
            region_id=test_region.id
        ), 4)
        items, total = area_service.list(db, AreaSearch())
        assert total >= 1
        db.delete(area)
        db.commit()
    
    def test_05_filter_region(self, db, area_service, test_region):
        """Filter by region_id"""
        area = area_service.create(db, AreaCreate(
            name=f"Test {time.time()}",
            code=f"AR-{time.time_ns()}",
            region_id=test_region.id
        ), 4)
        items, total = area_service.list(db, AreaSearch(region_id=test_region.id))
        assert total >= 1
        assert all(a.region_id == test_region.id for a in items)
        db.delete(area)
        db.commit()
    
    def test_06_soft_delete(self, db, area_service, test_region):
        """Soft delete"""
        area = area_service.create(db, AreaCreate(
            name=f"Test {time.time()}",
            code=f"AR-{time.time_ns()}",
            region_id=test_region.id
        ), 4)
        i, t = area_service.list(db, AreaSearch())
        deleted = area_service.soft_delete(db, area.id, 4)
        i2, t2 = area_service.list(db, AreaSearch())
        assert t2 < t
        db.delete(area)
        db.commit()
    
    def test_07_restore(self, db, area_service, test_region):
        """Restore"""
        area = area_service.create(db, AreaCreate(
            name=f"Test {time.time()}",
            code=f"AR-{time.time_ns()}",
            region_id=test_region.id
        ), 4)
        area_service.soft_delete(db, area.id, 4)
        i, t = area_service.list(db, AreaSearch())
        restored = area_service.restore(db, area.id, 4)
        i2, t2 = area_service.list(db, AreaSearch())
        assert t2 > t
        db.delete(area)
        db.commit()
    
    def test_08_unique_and_fk(self, db, area_service, test_region):
        """UNIQUE name + FK validation"""
        name = f"Unique Area {time.time()}"
        area = area_service.create(db, AreaCreate(
            name=name,
            code=f"AR-{time.time_ns()}",
            region_id=test_region.id
        ), 4)
        
        # Test UNIQUE
        from app.core.exceptions import DuplicateException, ValidationException
        with pytest.raises(DuplicateException):
            area_service.create(db, AreaCreate(
                name=name,
                code=f"AR-{time.time_ns()}",
                region_id=test_region.id
            ), 4)
        
        # Test FK
        with pytest.raises(ValidationException):
            area_service.create(db, AreaCreate(
                name=f"New {time.time()}",
                code=f"AR-{time.time_ns()}",
                region_id=999999
            ), 4)
        
        db.delete(area)
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
