"""
Reports Integration Tests
Report → ReportRuns flow
"""

import pytest
import time
from datetime import datetime

from app.core.database import SessionLocal
from app.schemas.report import ReportCreate, ReportUpdate
from app.schemas.report_run import ReportRunCreate, ReportRunUpdate, ReportRunSearch
from app.services.report_service import ReportService
from app.services.report_run_service import ReportRunService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


class TestReportsIntegration:
    """Report → Runs integration flow"""
    
    def test_01_create_report(self, db):
        """Create report"""
        report_service = ReportService()
        
        report = report_service.create(db, ReportCreate(
            code=f"INT-{int(time.time())}",
            name="Integration Test Report",
            type="ANALYTICAL",
            status="ACTIVE"
        ), 4)
        
        assert report.id is not None
        
        db.delete(report)
        db.commit()
    
    def test_02_create_run_for_report(self, db):
        """Create run for report"""
        report_service = ReportService()
        run_service = ReportRunService()
        
        report = report_service.create(db, ReportCreate(
            code=f"INT-{int(time.time())}",
            name="Test",
            type="FINANCIAL",
            status="ACTIVE"
        ), 4)
        
        run = run_service.create(db, ReportRunCreate(
            report_id=report.id,
            status="PENDING"
        ), 4)
        
        assert run.report_id == report.id
        assert run.run_number is not None
        
        db.delete(run)
        db.delete(report)
        db.commit()
    
    def test_03_update_run_status_flow(self, db):
        """Update run through status flow"""
        report_service = ReportService()
        run_service = ReportRunService()
        
        report = report_service.create(db, ReportCreate(
            code=f"INT-{int(time.time())}",
            name="Test",
            type="FINANCIAL",
            status="ACTIVE"
        ), 4)
        
        run = run_service.create(db, ReportRunCreate(
            report_id=report.id,
            status="PENDING"
        ), 4)
        
        # Update to RUNNING
        run = run_service.update(db, run.id, ReportRunUpdate(
            status="RUNNING",
            started_at=datetime.utcnow()
        ), 4)
        assert run.status == "RUNNING"
        
        # Complete
        run = run_service.update(db, run.id, ReportRunUpdate(
            status="SUCCESS",
            completed_at=datetime.utcnow(),
            result_count=50
        ), 4)
        assert run.status == "SUCCESS"
        
        db.delete(run)
        db.delete(report)
        db.commit()
    
    def test_04_list_runs_by_report(self, db):
        """List runs by report_id"""
        report_service = ReportService()
        run_service = ReportRunService()
        
        report = report_service.create(db, ReportCreate(
            code=f"INT-{int(time.time())}",
            name="Test",
            type="FINANCIAL",
            status="ACTIVE"
        ), 4)
        
        run1 = run_service.create(db, ReportRunCreate(report_id=report.id), 4)
        run2 = run_service.create(db, ReportRunCreate(report_id=report.id), 4)
        
        runs, total = run_service.list(db, ReportRunSearch(report_id=report.id))
        
        assert total == 2
        assert all(r.report_id == report.id for r in runs)
        
        db.delete(run1)
        db.delete(run2)
        db.delete(report)
        db.commit()
    
    def test_05_statistics_by_report(self, db):
        """Statistics by report"""
        report_service = ReportService()
        run_service = ReportRunService()
        
        report = report_service.create(db, ReportCreate(
            code=f"INT-{int(time.time())}",
            name="Test",
            type="FINANCIAL",
            status="ACTIVE"
        ), 4)
        
        run1 = run_service.create(db, ReportRunCreate(report_id=report.id, status="SUCCESS"), 4)
        run2 = run_service.create(db, ReportRunCreate(report_id=report.id, status="FAILED"), 4)
        
        stats = run_service.get_statistics(db, report.id)
        
        assert stats.total == 2
        assert stats.success_count >= 1
        assert stats.failed_count >= 1
        
        db.delete(run1)
        db.delete(run2)
        db.delete(report)
        db.commit()
    
    def test_06_update_report_trigger(self, db):
        """Update report + trigger"""
        report_service = ReportService()
        
        report = report_service.create(db, ReportCreate(
            code=f"INT-{int(time.time())}",
            name="Test",
            type="FINANCIAL",
            status="DRAFT"
        ), 4)
        
        fu = report.updated_at
        time.sleep(2)
        
        updated = report_service.update(db, report.id, ReportUpdate(status="ACTIVE"), 4)
        
        assert updated.updated_at > fu, "Trigger should work"
        
        db.delete(report)
        db.commit()
    
    def test_07_soft_delete_report(self, db):
        """Soft delete report doesn't delete runs"""
        report_service = ReportService()
        run_service = ReportRunService()
        
        report = report_service.create(db, ReportCreate(
            code=f"INT-{int(time.time())}",
            name="Test",
            type="FINANCIAL",
            status="ACTIVE"
        ), 4)
        
        run = run_service.create(db, ReportRunCreate(report_id=report.id), 4)
        
        # Soft delete report
        report_service.soft_delete(db, report.id, 4)
        
        # Run should still exist
        fetched_run = run_service.get_by_id(db, run.id)
        assert fetched_run is not None
        
        db.delete(run)
        db.delete(report)
        db.commit()
    
    def test_08_fk_validation(self, db):
        """FK validation"""
        run_service = ReportRunService()
        
        from app.core.exceptions import ValidationException
        with pytest.raises(ValidationException):
            run_service.create(db, ReportRunCreate(
                report_id=999999
            ), 4)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
