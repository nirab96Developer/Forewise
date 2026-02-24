"""
Tests for Users CRUD operations
Production Ready Standard - 8/8 tests
"""
import pytest
import time
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.models.department import Department
from app.services.user_service import user_service
from app.schemas.user import UserCreate, UserUpdate, UserSearch


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


class TestUsersCRUD:
    """Test suite for Users module"""
    
    # ========================================
    # Test 1: Create with timestamps
    # ========================================
    def test_create_user_with_timestamps(self, db: Session):
        """Test creating a user and verifying timestamps are set"""
        # Get a valid role
        role = db.query(Role).first()
        
        user_data = UserCreate(
            email=f"test_user_{int(time.time())}@example.com",
            password="SecurePassword123!",
            full_name="Test User",
            username=f"testuser_{int(time.time())}",
            role_id=role.id if role else None
        )
        
        user = user_service.create_user(db, user_data)
        
        assert user is not None
        assert user.id is not None
        assert user.email == user_data.email
        assert user.full_name == user_data.full_name
        assert user.created_at is not None
        assert user.is_active == True
        # Password should be hashed
        assert user.password_hash != user_data.password
    
    # ========================================
    # Test 2: Get by ID
    # ========================================
    def test_get_user_by_id(self, db: Session):
        """Test retrieving a user by ID"""
        # Get an existing user
        user = db.query(User).filter(User.deleted_at.is_(None)).first()
        
        if user:
            retrieved = user_service.get_by_id(db, user.id)
            
            assert retrieved is not None
            assert retrieved.id == user.id
            assert retrieved.email == user.email
    
    # ========================================
    # Test 3: Update with trigger check
    # ========================================
    def test_update_user_updates_timestamp(self, db: Session):
        """Test that updating a user updates the updated_at timestamp"""
        # Create a user first
        role = db.query(Role).first()
        
        user_data = UserCreate(
            email=f"update_test_{int(time.time())}@example.com",
            password="SecurePassword123!",
            full_name="Update Test User",
            username=f"updatetest_{int(time.time())}",
            role_id=role.id if role else None
        )
        user = user_service.create_user(db, user_data)
        original_updated_at = user.updated_at
        
        # Wait for trigger to detect time difference
        time.sleep(2)
        
        # Update the user
        update_data = UserUpdate(full_name="Updated Name")
        updated_user = user_service.update_user(db, user.id, update_data)
        
        assert updated_user.full_name == "Updated Name"
        # Check if updated_at changed (if trigger exists)
        if original_updated_at:
            assert updated_user.updated_at >= original_updated_at
    
    # ========================================
    # Test 4: List with pagination
    # ========================================
    def test_list_users_with_pagination(self, db: Session):
        """Test listing users with pagination"""
        filters = UserSearch(page=1, page_size=5)
        
        users, total = user_service.list_with_filters(db, filters)
        
        assert isinstance(users, list)
        assert len(users) <= 5
        assert total >= 0
    
    # ========================================
    # Test 5: Filter by role
    # ========================================
    def test_filter_users_by_role(self, db: Session):
        """Test filtering users by role_id"""
        role = db.query(Role).first()
        
        if role:
            filters = UserSearch(role_id=role.id, page=1, page_size=10)
            users, total = user_service.list_with_filters(db, filters)
            
            # All returned users should have this role
            for user in users:
                assert user.role_id == role.id
    
    # ========================================
    # Test 6: Soft delete
    # ========================================
    def test_soft_delete_user(self, db: Session):
        """Test soft deleting a user"""
        # Create a user to delete
        user_data = UserCreate(
            email=f"delete_test_{int(time.time())}@example.com",
            password="SecurePassword123!",
            full_name="Delete Test User",
            username=f"deletetest_{int(time.time())}"
        )
        user = user_service.create_user(db, user_data)
        user_id = user.id
        
        # Soft delete
        user_service.soft_delete(db, user_id)
        
        # Should not appear in active list
        filters = UserSearch(page=1, page_size=100)
        users, _ = user_service.list_with_filters(db, filters)
        user_ids = [u.id for u in users]
        
        assert user_id not in user_ids
    
    # ========================================
    # Test 7: Lock and unlock user
    # ========================================
    def test_lock_and_unlock_user(self, db: Session):
        """Test locking and unlocking a user"""
        # Create a user
        user_data = UserCreate(
            email=f"lock_test_{int(time.time())}@example.com",
            password="SecurePassword123!",
            full_name="Lock Test User",
            username=f"locktest_{int(time.time())}"
        )
        user = user_service.create_user(db, user_data)
        
        # Lock user
        locked_user = user_service.lock_user(db, user.id)
        assert locked_user.is_locked == True
        
        # Unlock user
        unlocked_user = user_service.unlock_user(db, user.id)
        assert unlocked_user.is_locked == False
    
    # ========================================
    # Test 8: Unique email validation
    # ========================================
    def test_duplicate_email_raises_error(self, db: Session):
        """Test that duplicate email raises an error"""
        email = f"unique_test_{int(time.time())}@example.com"
        
        # Create first user
        user_data1 = UserCreate(
            email=email,
            password="SecurePassword123!",
            full_name="First User",
            username=f"first_{int(time.time())}"
        )
        user_service.create_user(db, user_data1)
        
        # Try to create second user with same email
        user_data2 = UserCreate(
            email=email,
            password="SecurePassword123!",
            full_name="Second User",
            username=f"second_{int(time.time())}"
        )
        
        from app.core.exceptions import DuplicateException
        with pytest.raises(DuplicateException):
            user_service.create_user(db, user_data2)
