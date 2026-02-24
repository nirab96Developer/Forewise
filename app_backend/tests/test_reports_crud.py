"""
Report CRUD Tests
"""

import pytest
import time

from app.core.database import SessionLocal
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportUpdate, ReportSearch
from app.services.report_service import ReportService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def report_service():
    return ReportService()


class TestReportCRUD:
    
    def test_01_create(self, db, report_service):
        """Create"""
        report = report_service.create(db, ReportCreate(
            code=f"RPT-{int(time.time())}",
            name="Test Report",
            type="FINANCIAL",
            status="DRAFT"
        ), 4)
        assert report.id is not None
        assert report.created_at is not None
        db.delete(report)
        db.commit()
    
    def test_02_get(self, db, report_service):
        """Get"""
        report = report_service.create(db, ReportCreate(
            code=f"RPT-{int(time.time())}",
            name="Test",
            type="FINANCIAL",
            status="DRAFT"
        ), 4)
        fetched = report_service.get_by_id(db, report.id)
        assert fetched is not None
        db.delete(report)
        db.commit()
    
    def test_03_update_trigger(self, db, report_service):
        """Update + trigger"""
        report = report_service.create(db, ReportCreate(
            code=f"RPT-{int(time.time())}",
            name="Test",
            type="FINANCIAL",
            status="DRAFT"
        ), 4)
        fu = report.updated_at
        time.sleep(2)
        upd = report_service.update(db, report.id, ReportUpdate(name="Updated"), 4)
        assert upd.updated_at > fu
        db.delete(report)
        db.commit()
    
    def test_04_list(self, db, report_service):
        """List"""
        report = report_service.create(db, ReportCreate(
            code=f"RPT-{int(time.time())}",
            name="Test",
            type="FINANCIAL",
            status="DRAFT"
        ), 4)
        items, total = report_service.list(db, ReportSearch())
        assert total >= 1
        db.delete(report)
        db.commit()
    
    def test_05_by_code(self, db, report_service):
        """By code"""
        code = f"RPT-{int(time.time())}"
        report = report_service.create(db, ReportCreate(
            code=code,
            name="Test",
            type="FINANCIAL",
            status="DRAFT"
        ), 4)
        found = report_service.get_by_code(db, code)
        assert found is not None
        db.delete(report)
        db.commit()
    
    def test_06_soft_delete(self, db, report_service):
        """Soft delete"""
        report = report_service.create(db, ReportCreate(
            code=f"RPT-{int(time.time())}",
            name="Test",
            type="FINANCIAL",
            status="DRAFT"
        ), 4)
        i, t = report_service.list(db, ReportSearch())
        deleted = report_service.soft_delete(db, report.id, 4)
        i2, t2 = report_service.list(db, ReportSearch())
        assert t2 < t
        db.delete(report)
        db.commit()
    
    def test_07_restore(self, db, report_service):
        """Restore"""
        report = report_service.create(db, ReportCreate(
            code=f"RPT-{int(time.time())}",
            name="Test",
            type="FINANCIAL",
            status="DRAFT"
        ), 4)
        report_service.soft_delete(db, report.id, 4)
        i, t = report_service.list(db, ReportSearch())
        restored = report_service.restore(db, report.id, 4)
        i2, t2 = report_service.list(db, ReportSearch())
        assert t2 > t
        db.delete(report)
        db.commit()
    
    def test_08_unique_code(self, db, report_service):
        """UNIQUE code"""
        code = f"RPT-{int(time.time())}"
        report = report_service.create(db, ReportCreate(
            code=code,
            name="Test",
            type="FINANCIAL",
            status="DRAFT"
        ), 4)
        
        from app.core.exceptions import DuplicateException
        with pytest.raises(DuplicateException):
            report_service.create(db, ReportCreate(
                code=code,
                name="Duplicate",
                type="FINANCIAL",
                status="DRAFT"
            ), 4)
        
        db.delete(report)
        db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
