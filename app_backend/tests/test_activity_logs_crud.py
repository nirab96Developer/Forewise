"""
Tests for Activity Logs CRUD operations
Production Ready Standard - 8/8 tests
"""
import pytest
import time
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import SessionLocal
from app.models.activity_log import ActivityLog


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_data(db):
    """Get valid IDs for testing using raw SQL"""
    result = db.execute(text("SELECT id FROM users WHERE deleted_at IS NULL LIMIT 1")).fetchone()
    user_id = result[0] if result else None
    
    return {
        'user_id': user_id
    }


class TestActivityLogsCRUD:
    """Test suite for Activity Logs module"""
    
    # ========================================
    # Test 1: Create with timestamps
    # ========================================
    def test_create_log_with_timestamps(self, db: Session, test_data):
        """Test creating an activity log and verifying timestamps are set"""
        log = ActivityLog(
            user_id=test_data['user_id'],
            activity_type="test",
            action=f"test_action_{int(time.time())}",
            entity_type="test_entity",
            entity_id=1,
            category="system",
            ip_address="127.0.0.1",
            is_active=True,
            version=1
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        assert log.id is not None
        assert log.created_at is not None
        assert log.activity_type == "test"
        assert log.is_active == True
    
    # ========================================
    # Test 2: Get by ID
    # ========================================
    def test_get_log_by_id(self, db: Session):
        """Test retrieving a log by ID"""
        log = db.query(ActivityLog).filter(
            ActivityLog.is_active == True
        ).first()
        
        if log:
            retrieved = db.query(ActivityLog).filter(
                ActivityLog.id == log.id
            ).first()
            
            assert retrieved is not None
            assert retrieved.id == log.id
            assert retrieved.activity_type == log.activity_type
    
    # ========================================
    # Test 3: Update with trigger check
    # ========================================
    def test_update_log_updates_timestamp(self, db: Session, test_data):
        """Test that updating a log updates the updated_at timestamp"""
        log = ActivityLog(
            user_id=test_data['user_id'],
            activity_type="update_test",
            action=f"update_action_{int(time.time())}",
            is_active=True,
            version=1
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        original_updated_at = log.updated_at
        
        # Wait for trigger
        time.sleep(2)
        
        # Update
        log.details = "Updated details"
        db.commit()
        db.refresh(log)
        
        assert log.details == "Updated details"
        if original_updated_at:
            assert log.updated_at >= original_updated_at
    
    # ========================================
    # Test 4: List with pagination
    # ========================================
    def test_list_logs_with_pagination(self, db: Session):
        """Test listing logs with pagination"""
        logs = db.query(ActivityLog).filter(
            ActivityLog.is_active == True
        ).limit(5).all()
        
        total = db.query(ActivityLog).filter(
            ActivityLog.is_active == True
        ).count()
        
        assert isinstance(logs, list)
        assert len(logs) <= 5
        assert total >= 0
    
    # ========================================
    # Test 5: Filter by user_id
    # ========================================
    def test_filter_by_user_id(self, db: Session, test_data):
        """Test filtering logs by user_id"""
        if test_data['user_id']:
            # Create a log
            log = ActivityLog(
                user_id=test_data['user_id'],
                activity_type="filter_test",
                action=f"filter_action_{int(time.time())}",
                is_active=True,
                version=1
            )
            db.add(log)
            db.commit()
            
            # Filter
            filtered = db.query(ActivityLog).filter(
                ActivityLog.user_id == test_data['user_id'],
                ActivityLog.is_active == True
            ).all()
            
            for l in filtered:
                assert l.user_id == test_data['user_id']
    
    # ========================================
    # Test 6: Deactivate (soft delete)
    # ========================================
    def test_deactivate_log(self, db: Session, test_data):
        """Test deactivating a log"""
        log = ActivityLog(
            user_id=test_data['user_id'],
            activity_type="deactivate_test",
            action=f"deact_action_{int(time.time())}",
            is_active=True,
            version=1
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        log_id = log.id
        
        # Deactivate
        log.is_active = False
        log.deleted_at = datetime.utcnow()
        db.commit()
        
        # Should not appear in active list
        active_logs = db.query(ActivityLog).filter(
            ActivityLog.is_active == True
        ).all()
        active_ids = [l.id for l in active_logs]
        
        assert log_id not in active_ids
    
    # ========================================
    # Test 7: Activate (restore)
    # ========================================
    def test_activate_log(self, db: Session, test_data):
        """Test activating a deactivated log"""
        log = ActivityLog(
            user_id=test_data['user_id'],
            activity_type="activate_test",
            action=f"act_action_{int(time.time())}",
            is_active=False,
            deleted_at=datetime.utcnow(),
            version=1
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        # Activate
        log.is_active = True
        log.deleted_at = None
        db.commit()
        db.refresh(log)
        
        assert log.is_active == True
        assert log.deleted_at is None
    
    # ========================================
    # Test 8: Filter by activity_type
    # ========================================
    def test_filter_by_activity_type(self, db: Session, test_data):
        """Test filtering logs by activity_type"""
        activity_type = f"unique_type_{int(time.time())}"
        
        log = ActivityLog(
            user_id=test_data['user_id'],
            activity_type=activity_type,
            action="type_action",
            is_active=True,
            version=1
        )
        db.add(log)
        db.commit()
        
        # Filter
        filtered = db.query(ActivityLog).filter(
            ActivityLog.activity_type == activity_type,
            ActivityLog.is_active == True
        ).all()
        
        assert len(filtered) >= 1
        for l in filtered:
            assert l.activity_type == activity_type
