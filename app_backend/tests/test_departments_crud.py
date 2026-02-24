"""
Department CRUD Tests
"""

import pytest
import time

from app.core.database import SessionLocal
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentSearch
from app.services.department_service import DepartmentService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def dept_service():
    return DepartmentService()


class TestDepartmentCRUD:
    
    def test_01_create(self, db, dept_service):
        """Create with timestamps"""
        dept = dept_service.create(db, DepartmentCreate(
            code=f"DEPT-{int(time.time())}",
            name=f"Test Department {time.time()}"
        ), 4)
        assert dept.id is not None
        assert dept.created_at is not None
        assert dept.updated_at is not None
        db.delete(dept)
        db.commit()
    
    def test_02_get(self, db, dept_service):
        """Get by ID"""
        dept = dept_service.create(db, DepartmentCreate(
            code=f"DEPT-{int(time.time())}",
            name=f"Test {time.time()}"
        ), 4)
        fetched = dept_service.get_by_id(db, dept.id)
        assert fetched is not None
        db.delete(dept)
        db.commit()
    
    def test_03_update_trigger(self, db, dept_service):
        """Update + trigger"""
        dept = dept_service.create(db, DepartmentCreate(
            code=f"DEPT-{int(time.time())}",
            name=f"Test {time.time()}"
        ), 4)
        fu = dept.updated_at
        time.sleep(2)
        upd = dept_service.update(db, dept.id, DepartmentUpdate(description="Updated"), 4)
        assert upd.updated_at > fu, "Trigger should work"
        db.delete(dept)
        db.commit()
    
    def test_04_list(self, db, dept_service):
        """List with pagination"""
        dept = dept_service.create(db, DepartmentCreate(
            code=f"DEPT-{int(time.time())}",
            name=f"Test {time.time()}"
        ), 4)
        items, total = dept_service.list(db, DepartmentSearch())
        assert total >= 1
        db.delete(dept)
        db.commit()
    
    def test_05_by_code(self, db, dept_service):
        """Get by code"""
        code = f"DEPT-{int(time.time())}"
        dept = dept_service.create(db, DepartmentCreate(
            code=code,
            name=f"Test {time.time()}"
        ), 4)
        found = dept_service.get_by_code(db, code)
        assert found is not None
        assert found.code == code
        db.delete(dept)
        db.commit()
    
    def test_06_soft_delete(self, db, dept_service):
        """Soft delete"""
        dept = dept_service.create(db, DepartmentCreate(
            code=f"DEPT-{int(time.time())}",
            name=f"Test {time.time()}"
        ), 4)
        i, t = dept_service.list(db, DepartmentSearch())
        deleted = dept_service.soft_delete(db, dept.id, 4)
        i2, t2 = dept_service.list(db, DepartmentSearch())
        assert t2 < t
        db.delete(dept)
        db.commit()
    
    def test_07_restore(self, db, dept_service):
        """Restore"""
        dept = dept_service.create(db, DepartmentCreate(
            code=f"DEPT-{int(time.time())}",
            name=f"Test {time.time()}"
        ), 4)
        dept_service.soft_delete(db, dept.id, 4)
        i, t = dept_service.list(db, DepartmentSearch())
        restored = dept_service.restore(db, dept.id, 4)
        i2, t2 = dept_service.list(db, DepartmentSearch())
        assert t2 > t
        db.delete(dept)
        db.commit()
    
    def test_08_unique_code(self, db, dept_service):
        """UNIQUE code + self-ref validation"""
        code = f"UNIQ-{int(time.time())}"
        dept = dept_service.create(db, DepartmentCreate(
            code=code,
            name=f"Test {time.time()}"
        ), 4)
        
        # Test UNIQUE
        from app.core.exceptions import DuplicateException, ValidationException
        with pytest.raises(DuplicateException):
            dept_service.create(db, DepartmentCreate(
                code=code,
                name=f"Another {time.time()}"
            ), 4)
        
        # Test self-referential validation
        with pytest.raises(ValidationException):
            dept_service.update(db, dept.id, DepartmentUpdate(
                parent_department_id=dept.id  # Can't be own parent
            ), 4)
        
        db.delete(dept)
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
