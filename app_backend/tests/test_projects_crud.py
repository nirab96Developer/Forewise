"""
Project CRUD Tests
"""

import pytest
import time

from app.core.database import SessionLocal
from app.models.project import Project
from app.models.user import User
from app.models.region import Region
from app.models.area import Area
from app.models.location import Location
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectSearch
from app.services.project_service import ProjectService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def service():
    return ProjectService()


@pytest.fixture
def test_data(db):
    """Create test data for FKs"""
    # Get existing user
    user = db.query(User).first()
    
    # Create region
    region = Region(name=f"Test Region {time.time()}", code=f"RGN-{int(time.time())}")
    db.add(region)
    db.commit()
    db.refresh(region)
    
    # Create area
    area = Area(name=f"Test Area {time.time()}", code=f"AREA-{int(time.time())}", region_id=region.id)
    db.add(area)
    db.commit()
    db.refresh(area)
    
    # Create location
    location = Location(name=f"Test Location {time.time()}", code=f"LOC-{int(time.time())}", area_id=area.id)
    db.add(location)
    db.commit()
    db.refresh(location)
    
    yield {
        'manager_id': user.id if user else 4,
        'region_id': region.id,
        'area_id': area.id,
        'location_id': location.id,
        'region': region,
        'area': area,
        'location': location
    }
    
    db.delete(location)
    db.delete(area)
    db.delete(region)
    db.commit()


class TestProjectCRUD:
    
    def test_01_create(self, db, service, test_data):
        """Create with timestamps"""
        item = service.create(db, ProjectCreate(
            name=f"Test Project {time.time()}",
            code=f"PROJ-{int(time.time())}",
            manager_id=test_data['manager_id'],
            region_id=test_data['region_id'],
            area_id=test_data['area_id'],
            location_id=test_data['location_id']
        ), 4)
        assert item.id is not None
        assert item.created_at is not None
        db.delete(item)
        db.commit()
    
    def test_02_get(self, db, service, test_data):
        """Get by ID"""
        item = service.create(db, ProjectCreate(
            name=f"Test {time.time()}",
            manager_id=test_data['manager_id'],
            region_id=test_data['region_id'],
            area_id=test_data['area_id'],
            location_id=test_data['location_id']
        ), 4)
        fetched = service.get_by_id(db, item.id)
        assert fetched is not None
        db.delete(item)
        db.commit()
    
    def test_03_update_trigger(self, db, service, test_data):
        """Update + trigger"""
        item = service.create(db, ProjectCreate(
            name=f"Test {time.time()}",
            manager_id=test_data['manager_id'],
            region_id=test_data['region_id'],
            area_id=test_data['area_id'],
            location_id=test_data['location_id']
        ), 4)
        fu = item.updated_at
        time.sleep(2)
        upd = service.update(db, item.id, ProjectUpdate(description="Updated"), 4)
        assert upd.updated_at > fu, "Trigger should work"
        db.delete(item)
        db.commit()
    
    def test_04_list(self, db, service, test_data):
        """List with pagination"""
        item = service.create(db, ProjectCreate(
            name=f"Test {time.time()}",
            manager_id=test_data['manager_id'],
            region_id=test_data['region_id'],
            area_id=test_data['area_id'],
            location_id=test_data['location_id']
        ), 4)
        items, total = service.list(db, ProjectSearch())
        assert total >= 1
        db.delete(item)
        db.commit()
    
    def test_05_filter_region(self, db, service, test_data):
        """Filter by region_id"""
        item = service.create(db, ProjectCreate(
            name=f"Test {time.time()}",
            manager_id=test_data['manager_id'],
            region_id=test_data['region_id'],
            area_id=test_data['area_id'],
            location_id=test_data['location_id']
        ), 4)
        items, total = service.list(db, ProjectSearch(region_id=test_data['region_id']))
        assert total >= 1
        db.delete(item)
        db.commit()
    
    def test_06_soft_delete(self, db, service, test_data):
        """Soft delete"""
        item = service.create(db, ProjectCreate(
            name=f"Test {time.time()}",
            manager_id=test_data['manager_id'],
            region_id=test_data['region_id'],
            area_id=test_data['area_id'],
            location_id=test_data['location_id']
        ), 4)
        i, t = service.list(db, ProjectSearch())
        service.soft_delete(db, item.id, 4)
        i2, t2 = service.list(db, ProjectSearch())
        assert t2 < t
        db.delete(item)
        db.commit()
    
    def test_07_restore(self, db, service, test_data):
        """Restore"""
        item = service.create(db, ProjectCreate(
            name=f"Test {time.time()}",
            manager_id=test_data['manager_id'],
            region_id=test_data['region_id'],
            area_id=test_data['area_id'],
            location_id=test_data['location_id']
        ), 4)
        service.soft_delete(db, item.id, 4)
        i, t = service.list(db, ProjectSearch())
        service.restore(db, item.id, 4)
        i2, t2 = service.list(db, ProjectSearch())
        assert t2 > t
        db.delete(item)
        db.commit()
    
    def test_08_validation(self, db, service, test_data):
        """UNIQUE code + FK validation"""
        code = f"UNIQ-{int(time.time())}"
        item = service.create(db, ProjectCreate(
            name=f"Test {time.time()}",
            code=code,
            manager_id=test_data['manager_id'],
            region_id=test_data['region_id'],
            area_id=test_data['area_id'],
            location_id=test_data['location_id']
        ), 4)
        
        from app.core.exceptions import DuplicateException, ValidationException
        
        # Test UNIQUE code
        with pytest.raises(DuplicateException):
            service.create(db, ProjectCreate(
                name=f"Another {time.time()}",
                code=code,
                manager_id=test_data['manager_id'],
                region_id=test_data['region_id'],
                area_id=test_data['area_id'],
                location_id=test_data['location_id']
            ), 4)
        
        # Test FK validation
        with pytest.raises(ValidationException):
            service.create(db, ProjectCreate(
                name=f"Other {time.time()}",
                manager_id=test_data['manager_id'],
                region_id=999999,  # Invalid
                area_id=test_data['area_id'],
                location_id=test_data['location_id']
            ), 4)
        
        db.delete(item)
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
