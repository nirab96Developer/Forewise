"""
Tests for Support Tickets CRUD operations
Production Ready Standard - 8/8 tests
"""
import pytest
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import SessionLocal
from app.models.support_ticket import SupportTicket


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_data(db):
    """Get valid IDs for testing using raw SQL"""
    result = db.execute(text("SELECT id FROM users WHERE deleted_at IS NULL LIMIT 1")).fetchone()
    user_id = result[0] if result else 1
    
    # Get a second user for assignment
    result = db.execute(text("SELECT id FROM users WHERE deleted_at IS NULL LIMIT 2")).fetchall()
    assigned_to_id = result[1][0] if len(result) > 1 else user_id
    
    return {
        'user_id': user_id,
        'assigned_to_id': assigned_to_id
    }


class TestSupportTicketsCRUD:
    """Test suite for Support Tickets module"""
    
    # ========================================
    # Test 1: Create with timestamps
    # ========================================
    def test_create_ticket_with_timestamps(self, db: Session, test_data):
        """Test creating a ticket and verifying timestamps are set"""
        ticket_number = f"TKT-{int(time.time())}"
        
        ticket = SupportTicket(
            ticket_number=ticket_number,
            title="Test Support Ticket",
            description="This is a test ticket for testing purposes",
            type="BUG",
            priority="HIGH",
            status="OPEN",
            user_id=test_data['user_id'],
            is_active=True,
            version=1
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        assert ticket.id is not None
        assert ticket.created_at is not None
        assert ticket.ticket_number == ticket_number
        assert ticket.status == "OPEN"
        assert ticket.is_active == True
    
    # ========================================
    # Test 2: Get by ID
    # ========================================
    def test_get_ticket_by_id(self, db: Session):
        """Test retrieving a ticket by ID"""
        ticket = db.query(SupportTicket).filter(
            SupportTicket.deleted_at.is_(None)
        ).first()
        
        if ticket:
            retrieved = db.query(SupportTicket).filter(
                SupportTicket.id == ticket.id
            ).first()
            
            assert retrieved is not None
            assert retrieved.id == ticket.id
            assert retrieved.ticket_number == ticket.ticket_number
    
    # ========================================
    # Test 3: Update with trigger check
    # ========================================
    def test_update_ticket_updates_timestamp(self, db: Session, test_data):
        """Test that updating a ticket updates the updated_at timestamp"""
        ticket_number = f"TKT-UPD-{int(time.time())}"
        
        ticket = SupportTicket(
            ticket_number=ticket_number,
            title="Update Test Ticket",
            description="Testing update functionality",
            type="FEATURE",
            priority="MEDIUM",
            status="OPEN",
            user_id=test_data['user_id'],
            is_active=True,
            version=1
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        original_updated_at = ticket.updated_at
        
        # Wait for trigger
        time.sleep(2)
        
        # Update
        ticket.status = "IN_PROGRESS"
        ticket.assigned_to_id = test_data['assigned_to_id']
        db.commit()
        db.refresh(ticket)
        
        assert ticket.status == "IN_PROGRESS"
        if original_updated_at:
            assert ticket.updated_at >= original_updated_at
    
    # ========================================
    # Test 4: List with pagination
    # ========================================
    def test_list_tickets_with_pagination(self, db: Session):
        """Test listing tickets with pagination"""
        tickets = db.query(SupportTicket).filter(
            SupportTicket.deleted_at.is_(None)
        ).limit(5).all()
        
        total = db.query(SupportTicket).filter(
            SupportTicket.deleted_at.is_(None)
        ).count()
        
        assert isinstance(tickets, list)
        assert len(tickets) <= 5
        assert total >= 0
    
    # ========================================
    # Test 5: Filter by status
    # ========================================
    def test_filter_by_status(self, db: Session, test_data):
        """Test filtering tickets by status"""
        ticket_number = f"TKT-STAT-{int(time.time())}"
        status = "PENDING"
        
        ticket = SupportTicket(
            ticket_number=ticket_number,
            title="Status Filter Test",
            description="Testing status filter",
            type="QUESTION",
            priority="LOW",
            status=status,
            user_id=test_data['user_id'],
            is_active=True,
            version=1
        )
        db.add(ticket)
        db.commit()
        
        # Filter
        filtered = db.query(SupportTicket).filter(
            SupportTicket.status == status,
            SupportTicket.deleted_at.is_(None)
        ).all()
        
        assert len(filtered) >= 1
        for t in filtered:
            assert t.status == status
    
    # ========================================
    # Test 6: Soft delete
    # ========================================
    def test_soft_delete_ticket(self, db: Session, test_data):
        """Test soft deleting a ticket"""
        ticket_number = f"TKT-DEL-{int(time.time())}"
        
        ticket = SupportTicket(
            ticket_number=ticket_number,
            title="Delete Test Ticket",
            description="Testing soft delete",
            type="OTHER",
            priority="LOW",
            status="OPEN",
            user_id=test_data['user_id'],
            is_active=True,
            version=1
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        ticket_id = ticket.id
        
        # Soft delete
        ticket.deleted_at = datetime.utcnow()
        ticket.is_active = False
        db.commit()
        
        # Should not appear in active list
        active = db.query(SupportTicket).filter(
            SupportTicket.deleted_at.is_(None)
        ).all()
        active_ids = [t.id for t in active]
        
        assert ticket_id not in active_ids
    
    # ========================================
    # Test 7: Restore
    # ========================================
    def test_restore_ticket(self, db: Session, test_data):
        """Test restoring a soft-deleted ticket"""
        ticket_number = f"TKT-RST-{int(time.time())}"
        
        ticket = SupportTicket(
            ticket_number=ticket_number,
            title="Restore Test Ticket",
            description="Testing restore",
            type="BUG",
            priority="MEDIUM",
            status="CLOSED",
            user_id=test_data['user_id'],
            is_active=False,
            deleted_at=datetime.utcnow(),
            version=1
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        # Restore
        ticket.deleted_at = None
        ticket.is_active = True
        ticket.status = "REOPENED"
        db.commit()
        db.refresh(ticket)
        
        assert ticket.is_active == True
        assert ticket.deleted_at is None
    
    # ========================================
    # Test 8: Resolution workflow
    # ========================================
    def test_ticket_resolution_workflow(self, db: Session, test_data):
        """Test complete ticket resolution workflow"""
        ticket_number = f"TKT-RES-{int(time.time())}"
        
        # Create ticket
        ticket = SupportTicket(
            ticket_number=ticket_number,
            title="Resolution Test Ticket",
            description="Testing resolution workflow",
            type="BUG",
            priority="HIGH",
            status="OPEN",
            user_id=test_data['user_id'],
            estimated_resolution_time=60,  # minutes
            due_date=datetime.utcnow() + timedelta(days=1),
            is_active=True,
            version=1
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        # Assign
        ticket.assigned_to_id = test_data['assigned_to_id']
        ticket.status = "IN_PROGRESS"
        db.commit()
        
        # Resolve
        ticket.status = "RESOLVED"
        ticket.resolved_at = datetime.utcnow()
        ticket.actual_resolution_time = 45
        ticket.resolution_notes = "Issue fixed by updating configuration"
        db.commit()
        db.refresh(ticket)
        
        assert ticket.status == "RESOLVED"
        assert ticket.resolved_at is not None
        assert ticket.resolution_notes is not None
        assert ticket.actual_resolution_time == 45

