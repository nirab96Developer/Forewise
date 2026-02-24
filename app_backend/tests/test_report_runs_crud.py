"""
ReportRun CRUD Tests
"""

import pytest
import time

from app.core.database import SessionLocal
from app.models.report_run import ReportRun
from app.models.report import Report
from app.schemas.report_run import ReportRunCreate, ReportRunUpdate, ReportRunSearch
from app.services.report_run_service import ReportRunService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def report_run_service():
    return ReportRunService()


@pytest.fixture
def test_report(db):
    """Create test report"""
    report = Report(
        code=f"RPT-{int(time.time())}",
        name="Test Report",
        type="FINANCIAL",
        status="ACTIVE",
        created_by_id=4,
        requires_approval=False,
        max_execution_time=300,
        is_scheduled=False
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


class TestReportRunCRUD:
    
    def test_01_create(self, db, report_run_service, test_report):
        """Create"""
        run = report_run_service.create(db, ReportRunCreate(
            report_id=test_report.id,
            status="PENDING"
        ), 4)
        assert run.id is not None
        assert run.run_number is not None
        assert run.created_at is not None
        db.delete(run)
        db.delete(test_report)
        db.commit()
    
    def test_02_get(self, db, report_run_service, test_report):
        """Get"""
        run = report_run_service.create(db, ReportRunCreate(
            report_id=test_report.id
        ), 4)
        fetched = report_run_service.get_by_id(db, run.id)
        assert fetched is not None
        db.delete(run)
        db.delete(test_report)
        db.commit()
    
    def test_03_update_trigger(self, db, report_run_service, test_report):
        """Update + trigger"""
        run = report_run_service.create(db, ReportRunCreate(
            report_id=test_report.id
        ), 4)
        fu = run.updated_at
        time.sleep(2)
        upd = report_run_service.update(db, run.id, ReportRunUpdate(status="RUNNING"), 4)
        assert upd.updated_at > fu
        db.delete(run)
        db.delete(test_report)
        db.commit()
    
    def test_04_list(self, db, report_run_service, test_report):
        """List"""
        run = report_run_service.create(db, ReportRunCreate(
            report_id=test_report.id
        ), 4)
        items, total = report_run_service.list(db, ReportRunSearch())
        assert total >= 1
        db.delete(run)
        db.delete(test_report)
        db.commit()
    
    def test_05_by_report(self, db, report_run_service, test_report):
        """Filter by report_id"""
        run = report_run_service.create(db, ReportRunCreate(
            report_id=test_report.id
        ), 4)
        items, total = report_run_service.list(db, ReportRunSearch(report_id=test_report.id))
        assert any(r.id == run.id for r in items)
        db.delete(run)
        db.delete(test_report)
        db.commit()
    
    def test_06_statistics(self, db, report_run_service, test_report):
        """Statistics"""
        run = report_run_service.create(db, ReportRunCreate(
            report_id=test_report.id,
            status="SUCCESS"
        ), 4)
        stats = report_run_service.get_statistics(db, test_report.id)
        assert stats.total >= 1
        db.delete(run)
        db.delete(test_report)
        db.commit()
    
    def test_07_update_status_flow(self, db, report_run_service, test_report):
        """Update status flow"""
        run = report_run_service.create(db, ReportRunCreate(
            report_id=test_report.id,
            status="PENDING"
        ), 4)
        
        # Update to RUNNING
        run = report_run_service.update(db, run.id, ReportRunUpdate(status="RUNNING"), 4)
        assert run.status == "RUNNING"
        
        # Update to SUCCESS
        run = report_run_service.update(db, run.id, ReportRunUpdate(
            status="SUCCESS",
            result_count=100
        ), 4)
        assert run.status == "SUCCESS"
        
        db.delete(run)
        db.delete(test_report)
        db.commit()
    
    def test_08_fk_validation(self, db, report_run_service):
        """FK validation"""
        from app.core.exceptions import ValidationException
        with pytest.raises(ValidationException):
            report_run_service.create(db, ReportRunCreate(
                report_id=999999
            ), 4)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
