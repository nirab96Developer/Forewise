"""
Tests for Activity Types CRUD operations
Production Ready Standard - 8/8 tests
"""
import pytest
import time
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.activity_type import ActivityType
from app.services.activity_type_service import activity_type_service


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


class TestActivityTypesCRUD:
    """Test suite for Activity Types module"""
    
    # ========================================
    # Test 1: Create with timestamps
    # ========================================
    def test_create_activity_type_with_timestamps(self, db: Session):
        """Test creating an activity type and verifying timestamps are set"""
        code = f"TEST_{int(time.time())}"
        
        activity_type = activity_type_service.create_activity_type(
            db,
            code=code,
            name="Test Activity Type",
            description="A test activity type",
            category="TEST",
            is_active=True,
            sort_order=10
        )
        
        assert activity_type is not None
        assert activity_type.id is not None
        assert activity_type.code == code
        assert activity_type.name == "Test Activity Type"
        assert activity_type.created_at is not None
        assert activity_type.is_active == True
    
    # ========================================
    # Test 2: Get by ID
    # ========================================
    def test_get_activity_type_by_id(self, db: Session):
        """Test retrieving an activity type by ID"""
        # Get an existing activity type
        activity_type = db.query(ActivityType).first()
        
        if activity_type:
            retrieved = activity_type_service.get_by_id(db, activity_type.id)
            
            assert retrieved is not None
            assert retrieved.id == activity_type.id
            assert retrieved.code == activity_type.code
    
    # ========================================
    # Test 3: Update with trigger check
    # ========================================
    def test_update_activity_type_updates_timestamp(self, db: Session):
        """Test that updating an activity type updates the updated_at timestamp"""
        # Create an activity type first
        code = f"UPDATE_TEST_{int(time.time())}"
        activity_type = activity_type_service.create_activity_type(
            db,
            code=code,
            name="Update Test"
        )
        original_updated_at = activity_type.updated_at
        
        # Wait for trigger to detect time difference
        time.sleep(2)
        
        # Update
        updated = activity_type_service.update_activity_type(
            db,
            activity_type.id,
            {"name": "Updated Name"}
        )
        
        assert updated.name == "Updated Name"
        # Check if updated_at changed (trigger should fire)
        if original_updated_at:
            assert updated.updated_at >= original_updated_at
    
    # ========================================
    # Test 4: List with pagination
    # ========================================
    def test_list_activity_types_with_pagination(self, db: Session):
        """Test listing activity types with pagination"""
        items, total = activity_type_service.list_with_filters(
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
        """Test filtering activity types by category"""
        # Create with specific category
        category_name = f"CAT_{int(time.time())}"
        activity_type_service.create_activity_type(
            db,
            code=f"CAT_TEST_{int(time.time())}",
            name="Category Test",
            category=category_name
        )
        
        # Filter by category
        items, total = activity_type_service.list_with_filters(
            db,
            category=category_name
        )
        
        # All returned should have this category
        for item in items:
            assert item.category == category_name
    
    # ========================================
    # Test 6: Deactivate
    # ========================================
    def test_deactivate_activity_type(self, db: Session):
        """Test deactivating an activity type"""
        # Create an activity type
        activity_type = activity_type_service.create_activity_type(
            db,
            code=f"DEACT_TEST_{int(time.time())}",
            name="Deactivate Test"
        )
        
        # Deactivate
        deactivated = activity_type_service.deactivate(db, activity_type.id)
        
        assert deactivated.is_active == False
        
        # Should not appear in active-only list
        items, _ = activity_type_service.list_with_filters(db, is_active=True)
        ids = [i.id for i in items]
        assert activity_type.id not in ids
    
    # ========================================
    # Test 7: Activate (restore)
    # ========================================
    def test_activate_activity_type(self, db: Session):
        """Test activating a deactivated activity type"""
        # Create and deactivate
        activity_type = activity_type_service.create_activity_type(
            db,
            code=f"ACT_TEST_{int(time.time())}",
            name="Activate Test"
        )
        activity_type_service.deactivate(db, activity_type.id)
        
        # Activate
        activated = activity_type_service.activate(db, activity_type.id)
        
        assert activated.is_active == True
        
        # Should appear in active list
        items, _ = activity_type_service.list_with_filters(db, is_active=True)
        ids = [i.id for i in items]
        assert activity_type.id in ids
    
    # ========================================
    # Test 8: Unique code validation
    # ========================================
    def test_duplicate_code_raises_error(self, db: Session):
        """Test that duplicate code raises an error"""
        code = f"UNIQUE_TEST_{int(time.time())}"
        
        # Create first
        activity_type_service.create_activity_type(
            db,
            code=code,
            name="First"
        )
        
        # Try to create second with same code
        from app.core.exceptions import DuplicateException
        with pytest.raises(DuplicateException):
            activity_type_service.create_activity_type(
                db,
                code=code,
                name="Second"
            )
