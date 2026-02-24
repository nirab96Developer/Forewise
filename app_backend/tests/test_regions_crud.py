"""
Region CRUD Tests
"""

import pytest
import time

from app.core.database import SessionLocal
from app.models.region import Region
from app.schemas.region import RegionCreate, RegionUpdate, RegionSearch
from app.services.region_service import RegionService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def region_service():
    return RegionService()


class TestRegionCRUD:
    
    def test_01_create(self, db, region_service):
        """Create with timestamps"""
        region = region_service.create(db, RegionCreate(
            name=f"Test Region {time.time()}",
            code=f"RGN-{int(time.time())}"
        ), 4)
        assert region.id is not None
        assert region.created_at is not None
        assert region.updated_at is not None
        db.delete(region)
        db.commit()
    
    def test_02_get(self, db, region_service):
        """Get by ID"""
        region = region_service.create(db, RegionCreate(
            name=f"Test {time.time()}",
            code=f"RGN-{int(time.time())}"
        ), 4)
        fetched = region_service.get_by_id(db, region.id)
        assert fetched is not None
        db.delete(region)
        db.commit()
    
    def test_03_update_trigger(self, db, region_service):
        """Update + trigger"""
        region = region_service.create(db, RegionCreate(
            name=f"Test {time.time()}",
            code=f"RGN-{int(time.time())}"
        ), 4)
        fu = region.updated_at
        time.sleep(2)
        upd = region_service.update(db, region.id, RegionUpdate(description="Updated"), 4)
        assert upd.updated_at > fu, "Trigger should work"
        db.delete(region)
        db.commit()
    
    def test_04_list(self, db, region_service):
        """List with pagination"""
        region = region_service.create(db, RegionCreate(
            name=f"Test {time.time()}",
            code=f"RGN-{int(time.time())}"
        ), 4)
        items, total = region_service.list(db, RegionSearch())
        assert total >= 1
        db.delete(region)
        db.commit()
    
    def test_05_by_code(self, db, region_service):
        """Get by code"""
        code = f"RGN-{int(time.time())}"
        region = region_service.create(db, RegionCreate(
            name=f"Test {time.time()}",
            code=code
        ), 4)
        found = region_service.get_by_code(db, code)
        assert found is not None
        db.delete(region)
        db.commit()
    
    def test_06_soft_delete(self, db, region_service):
        """Soft delete"""
        region = region_service.create(db, RegionCreate(
            name=f"Test {time.time()}",
            code=f"RGN-{int(time.time())}"
        ), 4)
        i, t = region_service.list(db, RegionSearch())
        deleted = region_service.soft_delete(db, region.id, 4)
        i2, t2 = region_service.list(db, RegionSearch())
        assert t2 < t
        db.delete(region)
        db.commit()
    
    def test_07_restore(self, db, region_service):
        """Restore"""
        region = region_service.create(db, RegionCreate(
            name=f"Test {time.time()}",
            code=f"RGN-{int(time.time())}"
        ), 4)
        region_service.soft_delete(db, region.id, 4)
        i, t = region_service.list(db, RegionSearch())
        restored = region_service.restore(db, region.id, 4)
        i2, t2 = region_service.list(db, RegionSearch())
        assert t2 > t
        db.delete(region)
        db.commit()
    
    def test_08_unique_name(self, db, region_service):
        """UNIQUE name"""
        name = f"Unique Region {time.time()}"
        region = region_service.create(db, RegionCreate(
            name=name,
            code=f"RGN-{int(time.time())}"
        ), 4)
        
        from app.core.exceptions import DuplicateException
        with pytest.raises(DuplicateException):
            region_service.create(db, RegionCreate(
                name=name,
                code=f"RGN2-{int(time.time())}"
            ), 4)
        
        db.delete(region)
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
