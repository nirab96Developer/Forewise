"""
Location CRUD Tests
"""

import pytest
import time

from app.core.database import SessionLocal
from app.models.location import Location
from app.models.area import Area
from app.models.region import Region
from app.schemas.location import LocationCreate, LocationUpdate, LocationSearch
from app.services.location_service import LocationService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def service():
    return LocationService()


@pytest.fixture
def test_area(db):
    """Create test area for FK"""
    # Need region first
    region = Region(name=f"Test Region {time.time()}", code=f"RGN-{int(time.time())}")
    db.add(region)
    db.commit()
    db.refresh(region)
    
    area = Area(name=f"Test Area {time.time()}", code=f"AREA-{int(time.time())}", region_id=region.id)
    db.add(area)
    db.commit()
    db.refresh(area)
    
    yield area
    
    db.delete(area)
    db.delete(region)
    db.commit()


class TestLocationCRUD:
    
    def test_01_create(self, db, service, test_area):
        """Create with timestamps"""
        item = service.create(db, LocationCreate(
            code=f"LOC-{int(time.time())}",
            name=f"Test Location {time.time()}",
            area_id=test_area.id
        ), 4)
        assert item.id is not None
        assert item.created_at is not None
        db.delete(item)
        db.commit()
    
    def test_02_get(self, db, service, test_area):
        """Get by ID"""
        item = service.create(db, LocationCreate(
            code=f"LOC-{int(time.time())}",
            name=f"Test {time.time()}",
            area_id=test_area.id
        ), 4)
        fetched = service.get_by_id(db, item.id)
        assert fetched is not None
        db.delete(item)
        db.commit()
    
    def test_03_update_trigger(self, db, service, test_area):
        """Update + trigger"""
        item = service.create(db, LocationCreate(
            code=f"LOC-{int(time.time())}",
            name=f"Test {time.time()}",
            area_id=test_area.id
        ), 4)
        fu = item.updated_at
        time.sleep(2)
        upd = service.update(db, item.id, LocationUpdate(description="Updated"), 4)
        assert upd.updated_at > fu, "Trigger should work"
        db.delete(item)
        db.commit()
    
    def test_04_list(self, db, service, test_area):
        """List with pagination"""
        item = service.create(db, LocationCreate(
            code=f"LOC-{int(time.time())}",
            name=f"Test {time.time()}",
            area_id=test_area.id
        ), 4)
        items, total = service.list(db, LocationSearch())
        assert total >= 1
        db.delete(item)
        db.commit()
    
    def test_05_filter_area(self, db, service, test_area):
        """Filter by area_id"""
        item = service.create(db, LocationCreate(
            code=f"LOC-{int(time.time())}",
            name=f"Test {time.time()}",
            area_id=test_area.id
        ), 4)
        items, total = service.list(db, LocationSearch(area_id=test_area.id))
        assert total >= 1
        db.delete(item)
        db.commit()
    
    def test_06_soft_delete(self, db, service, test_area):
        """Soft delete"""
        item = service.create(db, LocationCreate(
            code=f"LOC-{int(time.time())}",
            name=f"Test {time.time()}",
            area_id=test_area.id
        ), 4)
        i, t = service.list(db, LocationSearch())
        service.soft_delete(db, item.id, 4)
        i2, t2 = service.list(db, LocationSearch())
        assert t2 < t
        db.delete(item)
        db.commit()
    
    def test_07_restore(self, db, service, test_area):
        """Restore"""
        item = service.create(db, LocationCreate(
            code=f"LOC-{int(time.time())}",
            name=f"Test {time.time()}",
            area_id=test_area.id
        ), 4)
        service.soft_delete(db, item.id, 4)
        i, t = service.list(db, LocationSearch())
        service.restore(db, item.id, 4)
        i2, t2 = service.list(db, LocationSearch())
        assert t2 > t
        db.delete(item)
        db.commit()
    
    def test_08_validation(self, db, service, test_area):
        """UNIQUE code + FK validation"""
        code = f"UNIQ-{int(time.time())}"
        item = service.create(db, LocationCreate(
            code=code,
            name=f"Test {time.time()}",
            area_id=test_area.id
        ), 4)
        
        from app.core.exceptions import DuplicateException, ValidationException
        
        # Test UNIQUE code
        with pytest.raises(DuplicateException):
            service.create(db, LocationCreate(
                code=code,
                name=f"Another {time.time()}",
                area_id=test_area.id
            ), 4)
        
        # Test FK validation
        with pytest.raises(ValidationException):
            service.create(db, LocationCreate(
                code=f"OTHER-{int(time.time())}",
                name=f"Other {time.time()}",
                area_id=999999
            ), 4)
        
        db.delete(item)
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
