"""
Integration Test: Work Orders → Worklogs Flow
Verifies work order → worklogs relationship works
"""

import pytest
import time
from datetime import date
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.project import Project
from app.models.equipment import Equipment
from app.models.activity_type import ActivityType
from app.schemas.work_order import WorkOrderCreate
from app.schemas.worklog import WorklogCreate, WorklogSearch
from app.services.work_order_service import WorkOrderService
from app.services.worklog_service import WorklogService


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_data(db):
    """Get valid IDs"""
    project = db.query(Project).filter(Project.is_active == True).first()
    equipment = db.query(Equipment).filter(Equipment.is_active == True).first()
    activity = db.query(ActivityType).first()
    
    from app.models.equipment_model import EquipmentModel
    model = db.query(EquipmentModel).filter(EquipmentModel.is_active == True).first()
    if not model:
        model = EquipmentModel(name=f"TEST_MODEL_{int(time.time())}", is_active=True)
        db.add(model)
        db.commit()
        db.refresh(model)

    return {
        'project_id': project.id if project else 1,
        'equipment_id': equipment.id if equipment else 1,
        'equipment_model_id': model.id,
        'activity_type_id': activity.id if activity else 1,
        'user_id': 4
    }


class TestWorkOrderWorklogsIntegration:
    """Work Order → Worklogs integration flow"""
    
    def test_01_create_work_order(self, db, test_data):
        """Create work order"""
        wo_service = WorkOrderService()
        
        wo = wo_service.create(db, WorkOrderCreate(requested_equipment_model_id=test_data['equipment_model_id'], 
            title="Integration Test WO",
            project_id=test_data['project_id']
        ), test_data['user_id'])
        
        assert wo.id is not None
        assert wo.order_number is not None
        
        # Cleanup
        db.delete(wo)
        db.commit()
    
    def test_02_create_worklogs_under_work_order(self, db, test_data):
        """Create 2 worklogs under same work order"""
        wo_service = WorkOrderService()
        wl_service = WorklogService()
        
        wo = wo_service.create(db, WorkOrderCreate(requested_equipment_model_id=test_data['equipment_model_id'], 
            title="Test WO",
            project_id=test_data['project_id']
        ), test_data['user_id'])
        
        wl1 = wl_service.create(db, WorklogCreate(
            work_order_id=wo.id,
            user_id=test_data['user_id'],
            project_id=test_data['project_id'],
            activity_type_id=test_data['activity_type_id'],
            equipment_id=test_data['equipment_id'],
            report_date=date.today(),
            work_hours=Decimal('8')
        ), test_data['user_id'])
        
        wl2 = wl_service.create(db, WorklogCreate(
            work_order_id=wo.id,
            user_id=test_data['user_id'],
            project_id=test_data['project_id'],
            activity_type_id=test_data['activity_type_id'],
            equipment_id=test_data['equipment_id'],
            report_date=date.today(),
            work_hours=Decimal('7')
        ), test_data['user_id'])
        
        assert wl1.work_order_id == wo.id
        assert wl2.work_order_id == wo.id
        
        # Cleanup - delete worklogs first (FK constraint)
        db.delete(wl1)
        db.delete(wl2)
        db.commit()
        db.delete(wo)
        db.commit()
    
    def test_03_list_worklogs_by_work_order(self, db, test_data):
        """List worklogs filtered by work_order_id"""
        wo_service = WorkOrderService()
        wl_service = WorklogService()
        
        wo = wo_service.create(db, WorkOrderCreate(requested_equipment_model_id=test_data['equipment_model_id'], 
            title="Test WO",
            project_id=test_data['project_id']
        ), test_data['user_id'])
        
        wl1 = wl_service.create(db, WorklogCreate(
            work_order_id=wo.id,
            user_id=test_data['user_id'],
            project_id=test_data['project_id'],
            activity_type_id=test_data['activity_type_id'],
            equipment_id=test_data['equipment_id'],
            report_date=date.today(),
            work_hours=Decimal('8')
        ), test_data['user_id'])
        
        wl2 = wl_service.create(db, WorklogCreate(
            work_order_id=wo.id,
            user_id=test_data['user_id'],
            project_id=test_data['project_id'],
            activity_type_id=test_data['activity_type_id'],
            equipment_id=test_data['equipment_id'],
            report_date=date.today(),
            work_hours=Decimal('7')
        ), test_data['user_id'])
        
        # List worklogs by work_order
        worklogs, total = wl_service.list(db, WorklogSearch(work_order_id=wo.id))
        
        assert total == 2
        assert all(wl.work_order_id == wo.id for wl in worklogs)
        
        # Cleanup - delete worklogs first (FK constraint)
        db.delete(wl1)
        db.delete(wl2)
        db.commit()
        db.delete(wo)
        db.commit()
    
    def test_04_update_worklog_trigger(self, db, test_data):
        """Update worklog + verify trigger"""
        wo_service = WorkOrderService()
        wl_service = WorklogService()
        
        wo = wo_service.create(db, WorkOrderCreate(requested_equipment_model_id=test_data['equipment_model_id'], 
            title="Test WO",
            project_id=test_data['project_id']
        ), test_data['user_id'])
        
        wl = wl_service.create(db, WorklogCreate(
            work_order_id=wo.id,
            user_id=test_data['user_id'],
            project_id=test_data['project_id'],
            activity_type_id=test_data['activity_type_id'],
            equipment_id=test_data['equipment_id'],
            report_date=date.today(),
            work_hours=Decimal('8')
        ), test_data['user_id'])
        
        fu = wl.updated_at
        time.sleep(2)
        
        from app.schemas.worklog import WorklogUpdate
        updated = wl_service.update(db, wl.id, WorklogUpdate(work_hours=Decimal('9')), test_data['user_id'])
        
        assert updated.updated_at > fu, "Trigger should work"
        
        # Cleanup - delete worklog first (FK constraint)
        db.delete(wl)
        db.commit()
        db.delete(wo)
        db.commit()
    
    def test_05_deactivate_worklog(self, db, test_data):
        """Deactivate worklog filters from list"""
        wo_service = WorkOrderService()
        wl_service = WorklogService()
        
        wo = wo_service.create(db, WorkOrderCreate(requested_equipment_model_id=test_data['equipment_model_id'], 
            title="Test WO",
            project_id=test_data['project_id']
        ), test_data['user_id'])
        
        wl = wl_service.create(db, WorklogCreate(
            work_order_id=wo.id,
            user_id=test_data['user_id'],
            project_id=test_data['project_id'],
            activity_type_id=test_data['activity_type_id'],
            equipment_id=test_data['equipment_id'],
            report_date=date.today(),
            work_hours=Decimal('8')
        ), test_data['user_id'])
        
        # List before
        wls_before, total_before = wl_service.list(db, WorklogSearch(work_order_id=wo.id))
        
        # Deactivate
        wl_service.deactivate(db, wl.id, test_data['user_id'])
        
        # List after
        wls_after, total_after = wl_service.list(db, WorklogSearch(work_order_id=wo.id))
        
        assert total_after < total_before, "Deactivated worklog should be filtered"
        
        # Cleanup - delete worklog first (FK constraint)
        db.delete(wl)
        db.commit()
        db.delete(wo)
        db.commit()
    
    def test_06_activate_worklog(self, db, test_data):
        """Activate worklog returns to list"""
        wo_service = WorkOrderService()
        wl_service = WorklogService()
        
        wo = wo_service.create(db, WorkOrderCreate(requested_equipment_model_id=test_data['equipment_model_id'], 
            title="Test WO",
            project_id=test_data['project_id']
        ), test_data['user_id'])
        
        wl = wl_service.create(db, WorklogCreate(
            work_order_id=wo.id,
            user_id=test_data['user_id'],
            project_id=test_data['project_id'],
            activity_type_id=test_data['activity_type_id'],
            equipment_id=test_data['equipment_id'],
            report_date=date.today(),
            work_hours=Decimal('8')
        ), test_data['user_id'])
        
        # Deactivate
        wl_service.deactivate(db, wl.id, test_data['user_id'])
        wls_deact, total_deact = wl_service.list(db, WorklogSearch(work_order_id=wo.id))
        
        # Activate
        wl_service.activate(db, wl.id, test_data['user_id'])
        wls_act, total_act = wl_service.list(db, WorklogSearch(work_order_id=wo.id))
        
        assert total_act > total_deact, "Activated worklog should return"
        
        # Cleanup - delete worklog first (FK constraint)
        db.delete(wl)
        db.commit()
        db.delete(wo)
        db.commit()
    
    def test_07_soft_delete_work_order_policy(self, db, test_data):
        """Soft delete work order (verify policy)"""
        wo_service = WorkOrderService()
        
        wo = wo_service.create(db, WorkOrderCreate(requested_equipment_model_id=test_data['equipment_model_id'], 
            title="Test WO",
            project_id=test_data['project_id'],
            status="PENDING"  # Not ACTIVE - should be deletable
        ), test_data['user_id'])
        
        # Should be able to soft delete PENDING work order
        deleted = wo_service.soft_delete(db, wo.id, test_data['user_id'])
        
        assert deleted.deleted_at is not None
        
        # Cleanup
        db.delete(wo)
        db.commit()
    
    def test_08_fk_validation_invalid_work_order(self, db, test_data):
        """FK validation: invalid work_order_id"""
        wl_service = WorklogService()
        
        from app.core.exceptions import ValidationException
        with pytest.raises(ValidationException):
            wl_service.create(db, WorklogCreate(
                work_order_id=999999,
                user_id=test_data['user_id'],
                project_id=test_data['project_id'],
                activity_type_id=test_data['activity_type_id'],
                equipment_id=test_data['equipment_id'],
                report_date=date.today(),
                work_hours=Decimal('8')
            ), test_data['user_id'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
