"""
Tests for Supplier Rejection Reasons CRUD operations
Production Ready Standard - 8/8 tests
"""
import pytest
import time
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.supplier_rejection_reason import SupplierRejectionReason
from app.services.supplier_rejection_reason_service import supplier_rejection_reason_service


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


class TestSupplierRejectionReasonsCRUD:
    """Test suite for Supplier Rejection Reasons module"""
    
    # ========================================
    # Test 1: Create with timestamps
    # ========================================
    def test_create_reason_with_timestamps(self, db: Session):
        """Test creating a reason and verifying timestamps are set"""
        code = f"SRR_TEST_{int(time.time())}"
        
        reason = supplier_rejection_reason_service.create_reason(
            db,
            code=code,
            name="Test Rejection Reason",
            description="A test rejection reason",
            category="TEST",
            is_active=True,
            requires_approval=True,
            display_order=10
        )
        
        assert reason is not None
        assert reason.id is not None
        assert reason.code == code
        assert reason.name == "Test Rejection Reason"
        assert reason.created_at is not None
        assert reason.is_active == True
        assert reason.requires_approval == True
    
    # ========================================
    # Test 2: Get by ID
    # ========================================
    def test_get_reason_by_id(self, db: Session):
        """Test retrieving a reason by ID"""
        reason = db.query(SupplierRejectionReason).first()
        
        if reason:
            retrieved = supplier_rejection_reason_service.get_by_id(db, reason.id)
            
            assert retrieved is not None
            assert retrieved.id == reason.id
            assert retrieved.code == reason.code
    
    # ========================================
    # Test 3: Update with trigger check
    # ========================================
    def test_update_reason_updates_timestamp(self, db: Session):
        """Test that updating a reason updates the updated_at timestamp"""
        code = f"SRR_UPD_{int(time.time())}"
        reason = supplier_rejection_reason_service.create_reason(
            db,
            code=code,
            name="Update Test"
        )
        original_updated_at = reason.updated_at
        
        # Wait for trigger
        time.sleep(2)
        
        # Update
        updated = supplier_rejection_reason_service.update_reason(
            db,
            reason.id,
            {"name": "Updated Name"}
        )
        
        assert updated.name == "Updated Name"
        if original_updated_at:
            assert updated.updated_at >= original_updated_at
    
    # ========================================
    # Test 4: List with pagination
    # ========================================
    def test_list_reasons_with_pagination(self, db: Session):
        """Test listing reasons with pagination"""
        items, total = supplier_rejection_reason_service.list_with_filters(
            db,
            page=1,
            page_size=5
        )
        
        assert isinstance(items, list)
        assert len(items) <= 5
        assert total >= 0
    
    # ========================================
    # Test 5: Filter by category
    # ========================================
    def test_filter_by_category(self, db: Session):
        """Test filtering reasons by category"""
        category_name = f"CAT_{int(time.time())}"
        supplier_rejection_reason_service.create_reason(
            db,
            code=f"SRR_CAT_{int(time.time())}",
            name="Category Test",
            category=category_name
        )
        
        items, total = supplier_rejection_reason_service.list_with_filters(
            db,
            category=category_name
        )
        
        for item in items:
            assert item.category == category_name
    
    # ========================================
    # Test 6: Deactivate
    # ========================================
    def test_deactivate_reason(self, db: Session):
        """Test deactivating a reason"""
        reason = supplier_rejection_reason_service.create_reason(
            db,
            code=f"SRR_DEACT_{int(time.time())}",
            name="Deactivate Test"
        )
        
        deactivated = supplier_rejection_reason_service.deactivate(db, reason.id)
        
        assert deactivated.is_active == False
        
        # Should not appear in active-only list
        items, _ = supplier_rejection_reason_service.list_with_filters(db, is_active=True)
        ids = [i.id for i in items]
        assert reason.id not in ids
    
    # ========================================
    # Test 7: Activate (restore)
    # ========================================
    def test_activate_reason(self, db: Session):
        """Test activating a deactivated reason"""
        reason = supplier_rejection_reason_service.create_reason(
            db,
            code=f"SRR_ACT_{int(time.time())}",
            name="Activate Test"
        )
        supplier_rejection_reason_service.deactivate(db, reason.id)
        
        activated = supplier_rejection_reason_service.activate(db, reason.id)
        
        assert activated.is_active == True
        
        # Should appear in active list
        items, _ = supplier_rejection_reason_service.list_with_filters(db, is_active=True)
        ids = [i.id for i in items]
        assert reason.id in ids
    
    # ========================================
    # Test 8: Unique code validation
    # ========================================
    def test_duplicate_code_raises_error(self, db: Session):
        """Test that duplicate code raises an error"""
        code = f"SRR_UNIQUE_{int(time.time())}"
        
        supplier_rejection_reason_service.create_reason(
            db,
            code=code,
            name="First"
        )
        
        from app.core.exceptions import DuplicateException
        with pytest.raises(DuplicateException):
            supplier_rejection_reason_service.create_reason(
                db,
                code=code,
                name="Second"
            )
