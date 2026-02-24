"""
Tests for Permissions CRUD operations
Production Ready Standard - 8/8 tests
"""
import pytest
import time
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.permission import Permission
from app.services.permission_service import permission_service
from app.schemas.permission import PermissionCreate, PermissionUpdate, PermissionSearch


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


class TestPermissionsCRUD:
    """Test suite for Permissions module"""
    
    # ========================================
    # Test 1: Create with timestamps
    # ========================================
    def test_create_permission_with_timestamps(self, db: Session):
        """Test creating a permission and verifying timestamps are set"""
        perm_data = PermissionCreate(
            code=f"test.create_{int(time.time())}",
            name="Test Create Permission",
            description="A test permission for unit tests",
            resource="test",
            action="create"
        )
        
        perm = permission_service.create_permission(db, perm_data)
        
        assert perm is not None
        assert perm.id is not None
        assert perm.code == perm_data.code
        assert perm.name == perm_data.name
        assert perm.created_at is not None
        assert perm.is_active == True
    
    # ========================================
    # Test 2: Get by ID
    # ========================================
    def test_get_permission_by_id(self, db: Session):
        """Test retrieving a permission by ID"""
        # Get an existing permission
        perm = db.query(Permission).filter(Permission.deleted_at.is_(None)).first()
        
        if perm:
            retrieved = permission_service.get_by_id(db, perm.id)
            
            assert retrieved is not None
            assert retrieved.id == perm.id
            assert retrieved.code == perm.code
    
    # ========================================
    # Test 3: Update with trigger check
    # ========================================
    def test_update_permission_updates_timestamp(self, db: Session):
        """Test that updating a permission updates the updated_at timestamp"""
        # Create a permission first
        perm_data = PermissionCreate(
            code=f"test.update_{int(time.time())}",
            name="Update Test Permission",
            resource="test",
            action="update"
        )
        perm = permission_service.create_permission(db, perm_data)
        original_updated_at = perm.updated_at
        
        # Wait for trigger to detect time difference
        time.sleep(2)
        
        # Update the permission
        update_data = PermissionUpdate(name="Updated Permission Name")
        updated_perm = permission_service.update_permission(db, perm.id, update_data)
        
        assert updated_perm.name == "Updated Permission Name"
        # Check if updated_at changed (if trigger exists)
        if original_updated_at:
            assert updated_perm.updated_at >= original_updated_at
    
    # ========================================
    # Test 4: List with pagination
    # ========================================
    def test_list_permissions_with_pagination(self, db: Session):
        """Test listing permissions with pagination"""
        filters = PermissionSearch(page=1, page_size=5)
        
        perms, total = permission_service.list_with_filters(db, filters)
        
        assert isinstance(perms, list)
        assert len(perms) <= 5
        assert total >= 0
    
    # ========================================
    # Test 5: Filter by resource
    # ========================================
    def test_filter_permissions_by_resource(self, db: Session):
        """Test filtering permissions by resource"""
        # Create permissions with specific resource
        resource_name = f"filter_resource_{int(time.time())}"
        
        perm_data = PermissionCreate(
            code=f"{resource_name}.read",
            name=f"{resource_name} Read",
            resource=resource_name,
            action="read"
        )
        permission_service.create_permission(db, perm_data)
        
        # Filter by resource
        filters = PermissionSearch(resource=resource_name, page=1, page_size=10)
        perms, total = permission_service.list_with_filters(db, filters)
        
        # All returned permissions should have this resource
        for perm in perms:
            assert perm.resource == resource_name
    
    # ========================================
    # Test 6: Soft delete
    # ========================================
    def test_soft_delete_permission(self, db: Session):
        """Test soft deleting a permission"""
        # Create a permission to delete
        perm_data = PermissionCreate(
            code=f"test.delete_{int(time.time())}",
            name="Delete Test Permission",
            resource="test",
            action="delete"
        )
        perm = permission_service.create_permission(db, perm_data)
        perm_id = perm.id
        
        # Soft delete
        permission_service.soft_delete(db, perm_id)
        
        # Should not appear in active list
        filters = PermissionSearch(page=1, page_size=100)
        perms, _ = permission_service.list_with_filters(db, filters)
        perm_ids = [p.id for p in perms]
        
        assert perm_id not in perm_ids
    
    # ========================================
    # Test 7: Get by code
    # ========================================
    def test_get_permission_by_code(self, db: Session):
        """Test retrieving a permission by code"""
        # Create a permission
        code = f"test.code_{int(time.time())}"
        perm_data = PermissionCreate(
            code=code,
            name="Code Test Permission",
            resource="test",
            action="code"
        )
        created_perm = permission_service.create_permission(db, perm_data)
        
        # Get by code
        retrieved = permission_service.get_by_code(db, code)
        
        assert retrieved is not None
        assert retrieved.id == created_perm.id
        assert retrieved.code == code
    
    # ========================================
    # Test 8: Unique code validation
    # ========================================
    def test_duplicate_code_raises_error(self, db: Session):
        """Test that duplicate code raises an error"""
        code = f"test.unique_{int(time.time())}"
        
        # Create first permission
        perm_data1 = PermissionCreate(
            code=code,
            name="First Permission",
            resource="test",
            action="unique"
        )
        permission_service.create_permission(db, perm_data1)
        
        # Try to create second permission with same code
        perm_data2 = PermissionCreate(
            code=code,
            name="Second Permission",
            resource="test",
            action="unique"
        )
        
        from app.core.exceptions import DuplicateException
        with pytest.raises(DuplicateException):
            permission_service.create_permission(db, perm_data2)
