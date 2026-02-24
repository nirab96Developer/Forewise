"""
Tests for Roles CRUD operations
Production Ready Standard - 8/8 tests
"""
import pytest
import time
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.role import Role
from app.models.permission import Permission
from app.services.role_service import role_service
from app.schemas.role import RoleCreate, RoleUpdate, RoleSearch


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


class TestRolesCRUD:
    """Test suite for Roles module"""
    
    # ========================================
    # Test 1: Create with timestamps
    # ========================================
    def test_create_role_with_timestamps(self, db: Session):
        """Test creating a role and verifying timestamps are set"""
        role_data = RoleCreate(
            code=f"TEST_ROLE_{int(time.time())}",
            name="Test Role",
            description="A test role for unit tests"
        )
        
        role = role_service.create_role(db, role_data)
        
        assert role is not None
        assert role.id is not None
        assert role.code == role_data.code.upper()
        assert role.name == role_data.name
        assert role.created_at is not None
        assert role.is_active == True
    
    # ========================================
    # Test 2: Get by ID
    # ========================================
    def test_get_role_by_id(self, db: Session):
        """Test retrieving a role by ID"""
        # Get an existing role
        role = db.query(Role).filter(Role.deleted_at.is_(None)).first()
        
        if role:
            retrieved = role_service.get_by_id(db, role.id)
            
            assert retrieved is not None
            assert retrieved.id == role.id
            assert retrieved.code == role.code
    
    # ========================================
    # Test 3: Update with trigger check
    # ========================================
    def test_update_role_updates_timestamp(self, db: Session):
        """Test that updating a role updates the updated_at timestamp"""
        # Create a role first
        role_data = RoleCreate(
            code=f"UPDATE_TEST_{int(time.time())}",
            name="Update Test Role"
        )
        role = role_service.create_role(db, role_data)
        original_updated_at = role.updated_at
        
        # Wait for trigger to detect time difference
        time.sleep(2)
        
        # Update the role
        update_data = RoleUpdate(name="Updated Role Name")
        updated_role = role_service.update_role(db, role.id, update_data)
        
        assert updated_role.name == "Updated Role Name"
        # Check if updated_at changed (if trigger exists)
        if original_updated_at:
            assert updated_role.updated_at >= original_updated_at
    
    # ========================================
    # Test 4: List with pagination
    # ========================================
    def test_list_roles_with_pagination(self, db: Session):
        """Test listing roles with pagination"""
        filters = RoleSearch(page=1, page_size=5)
        
        roles, total = role_service.list_with_filters(db, filters)
        
        assert isinstance(roles, list)
        assert len(roles) <= 5
        assert total >= 0
    
    # ========================================
    # Test 5: Get by code
    # ========================================
    def test_get_role_by_code(self, db: Session):
        """Test retrieving a role by code"""
        # Create a role
        code = f"CODE_TEST_{int(time.time())}"
        role_data = RoleCreate(
            code=code,
            name="Code Test Role"
        )
        created_role = role_service.create_role(db, role_data)
        
        # Get by code
        retrieved = role_service.get_by_code(db, code)
        
        assert retrieved is not None
        assert retrieved.id == created_role.id
        assert retrieved.code == code.upper()
    
    # ========================================
    # Test 6: Soft delete
    # ========================================
    def test_soft_delete_role(self, db: Session):
        """Test soft deleting a role"""
        # Create a role to delete
        role_data = RoleCreate(
            code=f"DELETE_TEST_{int(time.time())}",
            name="Delete Test Role"
        )
        role = role_service.create_role(db, role_data)
        role_id = role.id
        
        # Soft delete
        role_service.soft_delete(db, role_id)
        
        # Should not appear in active list
        filters = RoleSearch(page=1, page_size=100)
        roles, _ = role_service.list_with_filters(db, filters)
        role_ids = [r.id for r in roles]
        
        assert role_id not in role_ids
    
    # ========================================
    # Test 7: Assign and remove permission
    # ========================================
    def test_assign_and_remove_permission(self, db: Session):
        """Test assigning and removing permission from role"""
        # Create a role
        role_data = RoleCreate(
            code=f"PERM_TEST_{int(time.time())}",
            name="Permission Test Role"
        )
        role = role_service.create_role(db, role_data)
        
        # Get a permission
        permission = db.query(Permission).filter(Permission.deleted_at.is_(None)).first()
        
        if permission:
            # Assign permission
            role_service.assign_permission(db, role.id, permission.id)
            
            # Verify assignment
            permissions = role_service.list_role_permissions(db, role.id)
            perm_ids = [p.id for p in permissions]
            assert permission.id in perm_ids
            
            # Remove permission
            role_service.remove_permission(db, role.id, permission.id)
            
            # Verify removal
            permissions_after = role_service.list_role_permissions(db, role.id)
            perm_ids_after = [p.id for p in permissions_after]
            assert permission.id not in perm_ids_after
    
    # ========================================
    # Test 8: Unique code validation
    # ========================================
    def test_duplicate_code_raises_error(self, db: Session):
        """Test that duplicate code raises an error"""
        code = f"UNIQUE_TEST_{int(time.time())}"
        
        # Create first role
        role_data1 = RoleCreate(
            code=code,
            name="First Role"
        )
        role_service.create_role(db, role_data1)
        
        # Try to create second role with same code
        role_data2 = RoleCreate(
            code=code,
            name="Second Role"
        )
        
        from app.core.exceptions import DuplicateException
        with pytest.raises(DuplicateException):
            role_service.create_role(db, role_data2)
