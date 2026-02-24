"""
WorkOrder CRUD Tests - Production Ready Verification
Tests all CRUD operations + State Machine
"""

import pytest
import time
from datetime import date
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.work_order import WorkOrder
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderSearch,
    WorkOrderApproveRequest,
    WorkOrderRejectRequest
)
from app.services.work_order_service import WorkOrderService


@pytest.fixture
def db():
    """Database session fixture"""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def work_order_service():
    """WorkOrder service fixture"""
    return WorkOrderService()


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return 4  # Admin


@pytest.fixture
def test_project_id(db):
    """Get a valid project ID for testing"""
    from app.models.project import Project
    project = db.query(Project).filter(Project.is_active == True).first()
    if project:
        return project.id
    return 1  # Fallback


@pytest.fixture
def test_equipment_model_id(db):
    """Get a valid equipment model ID for testing"""
    from app.models.equipment_model import EquipmentModel

    model = db.query(EquipmentModel).filter(EquipmentModel.is_active == True).first()
    if model:
        return model.id

    model = EquipmentModel(name=f"TEST_MODEL_{int(time.time())}", is_active=True)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model.id


class TestWorkOrderCRUD:
    """WorkOrder CRUD test suite"""
    
    def test_01_create_work_order(self, db, work_order_service, test_user_id, test_project_id, test_equipment_model_id):
        """Test work order creation with auto-populated fields"""
        # Arrange
        data = WorkOrderCreate(requested_equipment_model_id=test_equipment_model_id, 
            title="Test Work Order",
            description="Testing work order creation",
            project_id=test_project_id,
            priority="MEDIUM",
            status="PENDING"
        )
        
        # Act
        work_order = work_order_service.create(db, data, test_user_id)
        
        # Assert
        assert work_order.id is not None
        assert work_order.order_number is not None, "order_number should be auto-generated"
        assert work_order.title == "Test Work Order"
        assert work_order.created_at is not None
        assert work_order.updated_at is not None
        assert work_order.version is not None
        assert work_order.status == "PENDING"
        
        # Cleanup
        db.delete(work_order)
        db.commit()
    
    def test_02_get_by_id(self, db, work_order_service, test_user_id, test_project_id, test_equipment_model_id):
        """Test getting work order by ID"""
        # Arrange
        work_order = work_order_service.create(
            db,
            WorkOrderCreate(requested_equipment_model_id=test_equipment_model_id, title="Test Get", project_id=test_project_id),
            test_user_id
        )
        
        # Act
        fetched = work_order_service.get_by_id(db, work_order.id)
        
        # Assert
        assert fetched is not None
        assert fetched.id == work_order.id
        assert fetched.title == "Test Get"
        
        # Cleanup
        db.delete(work_order)
        db.commit()
    
    def test_03_update_with_trigger(self, db, work_order_service, test_user_id, test_project_id, test_equipment_model_id):
        """Test update and verify DB trigger updates updated_at"""
        # Arrange
        work_order = work_order_service.create(
            db,
            WorkOrderCreate(requested_equipment_model_id=test_equipment_model_id, title="Test Update", project_id=test_project_id),
            test_user_id
        )
        original_updated_at = work_order.updated_at
        
        # Act
        time.sleep(2)
        updated = work_order_service.update(
            db,
            work_order.id,
            WorkOrderUpdate(title="Test Update - MODIFIED"),
            test_user_id
        )
        
        # Assert
        assert updated.title == "Test Update - MODIFIED"
        assert updated.updated_at > original_updated_at, "updated_at should be changed by DB trigger"
        
        # Cleanup
        db.delete(work_order)
        db.commit()
    
    def test_04_list_with_pagination(self, db, work_order_service, test_user_id, test_project_id, test_equipment_model_id):
        """Test listing work orders with pagination"""
        # Arrange
        wo1 = work_order_service.create(db, WorkOrderCreate(requested_equipment_model_id=test_equipment_model_id, title="List 1", project_id=test_project_id), test_user_id)
        wo2 = work_order_service.create(db, WorkOrderCreate(requested_equipment_model_id=test_equipment_model_id, title="List 2", project_id=test_project_id), test_user_id)
        
        # Act
        search = WorkOrderSearch(page=1, page_size=100)
        items, total = work_order_service.list(db, search)
        
        # Assert
        assert total >= 2
        assert len(items) <= 100
        assert any(wo.id == wo1.id for wo in items)
        assert any(wo.id == wo2.id for wo in items)
        
        # Cleanup
        db.delete(wo1)
        db.delete(wo2)
        db.commit()
    
    def test_05_soft_delete_filters_from_list(self, db, work_order_service, test_user_id, test_project_id, test_equipment_model_id):
        """Test soft delete sets deleted_at and filters from list"""
        # Arrange
        work_order = work_order_service.create(
            db,
            WorkOrderCreate(requested_equipment_model_id=test_equipment_model_id, title="Test Delete", project_id=test_project_id, status="PENDING"),
            test_user_id
        )
        items_before, total_before = work_order_service.list(db, WorkOrderSearch())
        
        # Act
        deleted = work_order_service.soft_delete(db, work_order.id, test_user_id)
        
        # Assert
        assert deleted.deleted_at is not None
        assert deleted.is_active == False
        
        # Verify not in list
        items_after, total_after = work_order_service.list(db, WorkOrderSearch())
        assert total_after < total_before
        
        # Cleanup
        db.delete(work_order)
        db.commit()
    
    def test_06_restore_brings_back_to_list(self, db, work_order_service, test_user_id, test_project_id, test_equipment_model_id):
        """Test restore clears deleted_at and brings back to list"""
        # Arrange
        work_order = work_order_service.create(
            db,
            WorkOrderCreate(requested_equipment_model_id=test_equipment_model_id, title="Test Restore", project_id=test_project_id),
            test_user_id
        )
        work_order_service.soft_delete(db, work_order.id, test_user_id)
        items_deleted, total_deleted = work_order_service.list(db, WorkOrderSearch())
        
        # Act
        restored = work_order_service.restore(db, work_order.id, test_user_id)
        
        # Assert
        assert restored.deleted_at is None
        assert restored.is_active == True
        
        # Verify back in list
        items_restored, total_restored = work_order_service.list(db, WorkOrderSearch())
        assert total_restored > total_deleted
        
        # Cleanup
        db.delete(work_order)
        db.commit()
    
    def test_07_state_machine_approve(self, db, work_order_service, test_user_id, test_project_id, test_equipment_model_id):
        """Test work order state machine: PENDING → APPROVED"""
        # Arrange - get an equipment
        from app.models.equipment import Equipment
        equipment = db.query(Equipment).filter(Equipment.is_active == True).first()
        
        if not equipment:
            pytest.skip("No active equipment available for testing")
        
        work_order = work_order_service.create(
            db,
            WorkOrderCreate(requested_equipment_model_id=test_equipment_model_id, title="Test Approve", project_id=test_project_id, status="PENDING"),
            test_user_id
        )
        
        # Act
        request = WorkOrderApproveRequest(equipment_id=equipment.id)
        approved = work_order_service.approve(db, work_order.id, request, test_user_id)
        
        # Assert
        assert approved.status == "APPROVED"
        assert approved.equipment_id == equipment.id
        
        # Cleanup
        db.delete(work_order)
        db.commit()
    
    def test_08_state_machine_reject(self, db, work_order_service, test_user_id, test_project_id, test_equipment_model_id):
        """Test work order state machine: PENDING → REJECTED"""
        # Arrange
        work_order = work_order_service.create(
            db,
            WorkOrderCreate(requested_equipment_model_id=test_equipment_model_id, title="Test Reject", project_id=test_project_id, status="PENDING"),
            test_user_id
        )
        
        # Get a rejection reason
        from app.models.supplier_rejection_reason import SupplierRejectionReason
        reason = db.query(SupplierRejectionReason).first()
        
        if not reason:
            # Create one for testing
            reason = SupplierRejectionReason(code="TEST", name="Test Reason")
            db.add(reason)
            db.commit()
        
        # Act
        request = WorkOrderRejectRequest(rejection_reason_id=reason.id, rejection_notes="Test rejection")
        rejected = work_order_service.reject(db, work_order.id, request, test_user_id)
        
        # Assert
        assert rejected.status == "REJECTED"
        assert rejected.rejection_reason_id == reason.id
        
        # Cleanup
        db.delete(work_order)
        db.commit()


class TestWorkOrderValidations:
    """WorkOrder validation test suite"""
    
    def test_order_number_auto_generated(self, db, work_order_service, test_user_id, test_project_id, test_equipment_model_id):
        """Test order_number is auto-generated and unique"""
        # Act
        wo1 = work_order_service.create(db, WorkOrderCreate(requested_equipment_model_id=test_equipment_model_id, title="WO1", project_id=test_project_id), test_user_id)
        wo2 = work_order_service.create(db, WorkOrderCreate(requested_equipment_model_id=test_equipment_model_id, title="WO2", project_id=test_project_id), test_user_id)
        
        # Assert
        assert wo1.order_number != wo2.order_number, "order_numbers should be unique"
        assert wo2.order_number > wo1.order_number, "order_number should increment"
        
        # Cleanup
        db.delete(wo1)
        db.delete(wo2)
        db.commit()
    
    def test_soft_delete_work_order_marks_deleted(self, db, work_order_service, test_user_id, test_project_id, test_equipment_model_id):
        """Test that soft delete marks work order as deleted (sets deleted_at)"""
        # Arrange
        work_order = work_order_service.create(
            db,
            WorkOrderCreate(requested_equipment_model_id=test_equipment_model_id, title="Test Delete", project_id=test_project_id),
            test_user_id
        )
        work_order_id = work_order.id
        
        # Act - soft delete the work order
        work_order_service.soft_delete(db, work_order_id, test_user_id)
        db.commit()
        
        # Assert - verify it's marked as deleted (not returned by default query)
        from app.core.exceptions import NotFoundException
        with pytest.raises(NotFoundException):
            work_order_service.get_by_id_or_404(db, work_order_id, include_deleted=False)
        
        # Verify we can still get it with include_deleted=True
        deleted_wo = work_order_service.get_by_id_or_404(db, work_order_id, include_deleted=True)
        assert deleted_wo.deleted_at is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
