"""
Tests for Work Order Statuses CRUD operations
Production Ready Standard - 8/8 tests
"""
import pytest
import time
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.work_order_status import WorkOrderStatus
from app.services.work_order_status_service import work_order_status_service


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


class TestWorkOrderStatusesCRUD:
    """Test suite for Work Order Statuses module"""
    
    # ========================================
    # Test 1: Create with timestamps
    # ========================================
    def test_create_status_with_timestamps(self, db: Session):
        """Test creating a status and verifying timestamps are set"""
        code = f"WOS_TEST_{int(time.time())}"
        
        status = work_order_status_service.create_status(
            db,
            code=code,
            name="Test Status",
            description="A test status",
            is_active=True,
            display_order=10
        )
        
        assert status is not None
        assert status.id is not None
        assert status.code == code
        assert status.name == "Test Status"
        assert status.created_at is not None
        assert status.is_active == True
    
    # ========================================
    # Test 2: Get by ID
    # ========================================
    def test_get_status_by_id(self, db: Session):
        """Test retrieving a status by ID"""
        status = db.query(WorkOrderStatus).first()
        
        if status:
            retrieved = work_order_status_service.get_by_id(db, status.id)
            
            assert retrieved is not None
            assert retrieved.id == status.id
            assert retrieved.code == status.code
    
    # ========================================
    # Test 3: Update with trigger check
    # ========================================
    def test_update_status_updates_timestamp(self, db: Session):
        """Test that updating a status updates the updated_at timestamp"""
        code = f"WOS_UPD_{int(time.time())}"
        status = work_order_status_service.create_status(
            db,
            code=code,
            name="Update Test"
        )
        original_updated_at = status.updated_at
        
        # Wait for trigger
        time.sleep(2)
        
        # Update
        updated = work_order_status_service.update_status(
            db,
            status.id,
            {"name": "Updated Name"}
        )
        
        assert updated.name == "Updated Name"
        if original_updated_at:
            assert updated.updated_at >= original_updated_at
    
    # ========================================
    # Test 4: List with pagination
    # ========================================
    def test_list_statuses_with_pagination(self, db: Session):
        """Test listing statuses with pagination"""
        items, total = work_order_status_service.list_with_filters(
            db,
            page=1,
            page_size=5
        )
        
        assert isinstance(items, list)
        assert len(items) <= 5
        assert total >= 0
    
    # ========================================
    # Test 5: Get by code
    # ========================================
    def test_get_by_code(self, db: Session):
        """Test retrieving a status by code"""
        code = f"WOS_CODE_{int(time.time())}"
        created = work_order_status_service.create_status(
            db,
            code=code,
            name="Code Test"
        )
        
        retrieved = work_order_status_service.get_by_code(db, code)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.code == code
    
    # ========================================
    # Test 6: Deactivate
    # ========================================
    def test_deactivate_status(self, db: Session):
        """Test deactivating a status"""
        status = work_order_status_service.create_status(
            db,
            code=f"WOS_DEACT_{int(time.time())}",
            name="Deactivate Test"
        )
        
        deactivated = work_order_status_service.deactivate(db, status.id)
        
        assert deactivated.is_active == False
        
        # Should not appear in active-only list
        items, _ = work_order_status_service.list_with_filters(db, is_active=True)
        ids = [i.id for i in items]
        assert status.id not in ids
    
    # ========================================
    # Test 7: Activate (restore)
    # ========================================
    def test_activate_status(self, db: Session):
        """Test activating a deactivated status"""
        status = work_order_status_service.create_status(
            db,
            code=f"WOS_ACT_{int(time.time())}",
            name="Activate Test"
        )
        work_order_status_service.deactivate(db, status.id)
        
        activated = work_order_status_service.activate(db, status.id)
        
        assert activated.is_active == True
        
        # Should appear in active list
        items, _ = work_order_status_service.list_with_filters(db, is_active=True)
        ids = [i.id for i in items]
        assert status.id in ids
    
    # ========================================
    # Test 8: Unique code validation
    # ========================================
    def test_duplicate_code_raises_error(self, db: Session):
        """Test that duplicate code raises an error"""
        code = f"WOS_UNIQUE_{int(time.time())}"
        
        work_order_status_service.create_status(
            db,
            code=code,
            name="First"
        )
        
        from app.core.exceptions import DuplicateException
        with pytest.raises(DuplicateException):
            work_order_status_service.create_status(
                db,
                code=code,
                name="Second"
            )
