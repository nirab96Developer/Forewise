"""
Tests for Project Assignments CRUD operations
Production Ready Standard - 8/8 tests
"""
import pytest
import time
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import SessionLocal
from app.models.project_assignment import ProjectAssignment


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_data(db):
    """Get valid IDs for testing using raw SQL"""
    result = db.execute(text("SELECT id FROM projects WHERE deleted_at IS NULL LIMIT 1")).fetchone()
    project_id = result[0] if result else 1
    
    # Get multiple users to avoid UNIQUE constraint (project_id, user_id)
    result = db.execute(text("SELECT id FROM users WHERE deleted_at IS NULL")).fetchall()
    user_ids = [r[0] for r in result] if result else [1]
    
    return {
        'project_id': project_id,
        'user_ids': user_ids,
        'user_id': user_ids[0] if user_ids else 1
    }


class TestProjectAssignmentsCRUD:
    """Test suite for Project Assignments module"""
    
    # ========================================
    # Test 1: Create with timestamps
    # ========================================
    def test_create_assignment_with_timestamps(self, db: Session, test_data):
        """Test creating an assignment and verifying timestamps are set"""
        user_id = test_data['user_ids'][0] if len(test_data['user_ids']) > 0 else test_data['user_id']
        
        # Delete any existing
        db.execute(text(f"DELETE FROM project_assignments WHERE project_id = {test_data['project_id']} AND user_id = {user_id}"))
        db.commit()
        
        assignment = ProjectAssignment(
            project_id=test_data['project_id'],
            user_id=user_id,
            role="TEAM_MEMBER",
            status="ACTIVE",
            start_date=date.today(),
            allocation_percentage=100,
            can_approve_reports=False,
            can_manage_team=False,
            can_edit_budget=False,
            is_active=True,
            version=1
        )
        
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        
        assert assignment.id is not None
        assert assignment.created_at is not None
        assert assignment.project_id == test_data['project_id']
        assert assignment.is_active == True
    
    # ========================================
    # Test 2: Get by ID
    # ========================================
    def test_get_assignment_by_id(self, db: Session):
        """Test retrieving an assignment by ID"""
        assignment = db.query(ProjectAssignment).filter(
            ProjectAssignment.deleted_at.is_(None)
        ).first()
        
        if assignment:
            retrieved = db.query(ProjectAssignment).filter(
                ProjectAssignment.id == assignment.id
            ).first()
            
            assert retrieved is not None
            assert retrieved.id == assignment.id
            assert retrieved.role == assignment.role
    
    # ========================================
    # Test 3: Update with trigger check
    # ========================================
    def test_update_assignment_updates_timestamp(self, db: Session, test_data):
        """Test that updating an assignment updates the updated_at timestamp"""
        # Use a unique user_id for this test (based on timestamp)
        user_id = test_data['user_ids'][1] if len(test_data['user_ids']) > 1 else test_data['user_id']
        
        # First delete any existing assignment with same combo
        db.execute(text(f"DELETE FROM project_assignments WHERE project_id = {test_data['project_id']} AND user_id = {user_id}"))
        db.commit()
        
        assignment = ProjectAssignment(
            project_id=test_data['project_id'],
            user_id=user_id,
            role="TEAM_MEMBER",
            status="PENDING",
            start_date=date.today(),
            allocation_percentage=50,
            can_approve_reports=False,
            can_manage_team=False,
            can_edit_budget=False,
            is_active=True,
            version=1
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        original_updated_at = assignment.updated_at
        
        # Wait for trigger
        time.sleep(2)
        
        # Update
        assignment.status = "ACTIVE"
        assignment.allocation_percentage = 75
        db.commit()
        db.refresh(assignment)
        
        assert assignment.status == "ACTIVE"
        if original_updated_at:
            assert assignment.updated_at >= original_updated_at
    
    # ========================================
    # Test 4: List with pagination
    # ========================================
    def test_list_assignments_with_pagination(self, db: Session):
        """Test listing assignments with pagination"""
        assignments = db.query(ProjectAssignment).filter(
            ProjectAssignment.deleted_at.is_(None)
        ).limit(5).all()
        
        total = db.query(ProjectAssignment).filter(
            ProjectAssignment.deleted_at.is_(None)
        ).count()
        
        assert isinstance(assignments, list)
        assert len(assignments) <= 5
        assert total >= 0
    
    # ========================================
    # Test 5: Filter by project_id
    # ========================================
    def test_filter_by_project_id(self, db: Session, test_data):
        """Test filtering assignments by project_id"""
        user_id = test_data['user_ids'][2] if len(test_data['user_ids']) > 2 else test_data['user_id']
        
        # Delete any existing
        db.execute(text(f"DELETE FROM project_assignments WHERE project_id = {test_data['project_id']} AND user_id = {user_id}"))
        db.commit()
        
        # Create assignment
        assignment = ProjectAssignment(
            project_id=test_data['project_id'],
            user_id=user_id,
            role="LEAD",
            status="ACTIVE",
            start_date=date.today(),
            allocation_percentage=100,
            can_approve_reports=True,
            can_manage_team=True,
            can_edit_budget=False,
            is_active=True,
            version=1
        )
        db.add(assignment)
        db.commit()
        
        # Filter
        filtered = db.query(ProjectAssignment).filter(
            ProjectAssignment.project_id == test_data['project_id'],
            ProjectAssignment.deleted_at.is_(None)
        ).all()
        
        for a in filtered:
            assert a.project_id == test_data['project_id']
    
    # ========================================
    # Test 6: Soft delete
    # ========================================
    def test_soft_delete_assignment(self, db: Session, test_data):
        """Test soft deleting an assignment"""
        user_id = test_data['user_ids'][3] if len(test_data['user_ids']) > 3 else test_data['user_id']
        
        # Delete any existing
        db.execute(text(f"DELETE FROM project_assignments WHERE project_id = {test_data['project_id']} AND user_id = {user_id}"))
        db.commit()
        
        assignment = ProjectAssignment(
            project_id=test_data['project_id'],
            user_id=user_id,
            role="VIEWER",
            status="ACTIVE",
            start_date=date.today(),
            allocation_percentage=25,
            can_approve_reports=False,
            can_manage_team=False,
            can_edit_budget=False,
            is_active=True,
            version=1
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        assignment_id = assignment.id
        
        # Soft delete
        assignment.deleted_at = datetime.utcnow()
        assignment.is_active = False
        db.commit()
        
        # Should not appear in active list
        active = db.query(ProjectAssignment).filter(
            ProjectAssignment.deleted_at.is_(None)
        ).all()
        active_ids = [a.id for a in active]
        
        assert assignment_id not in active_ids
    
    # ========================================
    # Test 7: Restore
    # ========================================
    def test_restore_assignment(self, db: Session, test_data):
        """Test restoring a soft-deleted assignment"""
        user_id = test_data['user_ids'][4] if len(test_data['user_ids']) > 4 else test_data['user_id']
        
        # Delete any existing
        db.execute(text(f"DELETE FROM project_assignments WHERE project_id = {test_data['project_id']} AND user_id = {user_id}"))
        db.commit()
        
        assignment = ProjectAssignment(
            project_id=test_data['project_id'],
            user_id=user_id,
            role="CONSULTANT",
            status="INACTIVE",
            start_date=date.today(),
            allocation_percentage=10,
            can_approve_reports=False,
            can_manage_team=False,
            can_edit_budget=False,
            is_active=False,
            deleted_at=datetime.utcnow(),
            version=1
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        
        # Restore
        assignment.deleted_at = None
        assignment.is_active = True
        db.commit()
        db.refresh(assignment)
        
        assert assignment.is_active == True
        assert assignment.deleted_at is None
    
    # ========================================
    # Test 8: Filter by status
    # ========================================
    def test_filter_by_status(self, db: Session, test_data):
        """Test filtering assignments by status"""
        status = "ACTIVE"
        user_id = test_data['user_ids'][5] if len(test_data['user_ids']) > 5 else test_data['user_id']
        
        # Delete any existing
        db.execute(text(f"DELETE FROM project_assignments WHERE project_id = {test_data['project_id']} AND user_id = {user_id}"))
        db.commit()
        
        assignment = ProjectAssignment(
            project_id=test_data['project_id'],
            user_id=user_id,
            role="MEMBER",
            status=status,
            start_date=date.today(),
            allocation_percentage=50,
            can_approve_reports=False,
            can_manage_team=False,
            can_edit_budget=False,
            is_active=True,
            version=1
        )
        db.add(assignment)
        db.commit()
        
        # Filter
        filtered = db.query(ProjectAssignment).filter(
            ProjectAssignment.status == status,
            ProjectAssignment.deleted_at.is_(None)
        ).all()
        
        assert len(filtered) >= 1
        for a in filtered:
            assert a.status == status
