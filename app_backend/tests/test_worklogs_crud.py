"""
Worklog CRUD Tests - Production Ready
"""

import pytest
import time
from datetime import date
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.worklog import Worklog
from app.models.work_order import WorkOrder
from app.models.user import User
from app.models.project import Project
from app.models.activity_type import ActivityType
from app.schemas.worklog import WorklogCreate, WorklogUpdate, WorklogSearch
from app.services.worklog_service import WorklogService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def worklog_service():
    return WorklogService()


@pytest.fixture
def test_data(db):
    """Get valid IDs for testing"""
    from app.models.equipment import Equipment
    
    wo = db.query(WorkOrder).first()
    user = db.query(User).first()
    project = db.query(Project).first()
    act_type = db.query(ActivityType).first()
    eq = db.query(Equipment).filter(Equipment.deleted_at.is_(None)).first()
    
    return {
        'work_order_id': wo.id if wo else 1,
        'user_id': user.id if user else 4,
        'project_id': project.id if project else 1,
        'activity_type_id': act_type.id if act_type else 1,
        'equipment_id': eq.id if eq else 1  # Required by CK_worklogs_equipment_required
    }


class TestWorklogCRUD:
    
    def test_01_create(self, db, worklog_service, test_data):
        """Create with timestamps"""
        data = WorklogCreate(
            report_date=date.today(),
            work_hours=Decimal('8.0'),
            **test_data
        )
        
        wl = worklog_service.create(db, data, test_data['user_id'])
        assert wl.id is not None
        assert wl.report_number is not None
        assert wl.created_at is not None
        assert wl.updated_at is not None
        
        db.delete(wl)
        db.commit()
    
    def test_02_get(self, db, worklog_service, test_data):
        """Get by ID"""
        wl = worklog_service.create(db, WorklogCreate(report_date=date.today(), work_hours=Decimal('8'), **test_data), test_data['user_id'])
        fetched = worklog_service.get_by_id(db, wl.id)
        assert fetched is not None
        db.delete(wl)
        db.commit()
    
    def test_03_update_trigger(self, db, worklog_service, test_data):
        """Update + trigger check"""
        wl = worklog_service.create(db, WorklogCreate(report_date=date.today(), work_hours=Decimal('8'), **test_data), test_data['user_id'])
        first_updated = wl.updated_at
        
        time.sleep(2)
        updated = worklog_service.update(db, wl.id, WorklogUpdate(work_hours=Decimal('9')), test_data['user_id'])
        assert updated.updated_at > first_updated, "Trigger should update updated_at"
        
        db.delete(wl)
        db.commit()
    
    def test_04_list(self, db, worklog_service, test_data):
        """List with pagination"""
        wl1 = worklog_service.create(db, WorklogCreate(report_date=date.today(), work_hours=Decimal('8'), **test_data), test_data['user_id'])
        wl2 = worklog_service.create(db, WorklogCreate(report_date=date.today(), work_hours=Decimal('7'), **test_data), test_data['user_id'])
        
        items, total = worklog_service.list(db, WorklogSearch())
        assert total >= 2
        
        db.delete(wl1)
        db.delete(wl2)
        db.commit()
    
    def test_05_filter_by_work_order(self, db, worklog_service, test_data):
        """Filter by work_order_id"""
        wl = worklog_service.create(db, WorklogCreate(report_date=date.today(), work_hours=Decimal('8'), **test_data), test_data['user_id'])
        
        items, total = worklog_service.list(db, WorklogSearch(work_order_id=test_data['work_order_id']))
        assert any(w.id == wl.id for w in items)
        
        db.delete(wl)
        db.commit()
    
    def test_06_deactivate(self, db, worklog_service, test_data):
        """Deactivate (is_active=False)"""
        wl = worklog_service.create(db, WorklogCreate(report_date=date.today(), work_hours=Decimal('8'), **test_data), test_data['user_id'])
        items_before, total_before = worklog_service.list(db, WorklogSearch())
        
        deactivated = worklog_service.deactivate(db, wl.id, test_data['user_id'])
        assert deactivated.is_active == False
        
        items_after, total_after = worklog_service.list(db, WorklogSearch())
        assert total_after < total_before
        
        db.delete(wl)
        db.commit()
    
    def test_07_activate(self, db, worklog_service, test_data):
        """Activate (is_active=True)"""
        wl = worklog_service.create(db, WorklogCreate(report_date=date.today(), work_hours=Decimal('8'), **test_data), test_data['user_id'])
        worklog_service.deactivate(db, wl.id, test_data['user_id'])
        items_deact, total_deact = worklog_service.list(db, WorklogSearch())
        
        activated = worklog_service.activate(db, wl.id, test_data['user_id'])
        assert activated.is_active == True
        
        items_act, total_act = worklog_service.list(db, WorklogSearch())
        assert total_act > total_deact
        
        db.delete(wl)
        db.commit()
    
    def test_08_fk_validation(self, db, worklog_service, test_data):
        """FK validation"""
        from app.core.exceptions import ValidationException
        
        bad_data = test_data.copy()
        bad_data['work_order_id'] = 999999
        
        with pytest.raises(ValidationException):
            worklog_service.create(db, WorklogCreate(report_date=date.today(), work_hours=Decimal('8'), **bad_data), test_data['user_id'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
