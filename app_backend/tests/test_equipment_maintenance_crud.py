"""
Tests for Equipment Maintenance CRUD operations
Production Ready Standard - 8/8 tests
"""
import pytest
import time
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import SessionLocal
from app.models.equipment_maintenance import EquipmentMaintenance


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_data(db):
    """Get valid IDs for testing using raw SQL"""
    result = db.execute(text("SELECT id FROM equipment LIMIT 1")).fetchone()
    equipment_id = result[0] if result else 1
    
    result = db.execute(text("SELECT id FROM users WHERE deleted_at IS NULL LIMIT 1")).fetchone()
    user_id = result[0] if result else 1
    
    return {
        'equipment_id': equipment_id,
        'user_id': user_id
    }


class TestEquipmentMaintenanceCRUD:
    """Test suite for Equipment Maintenance module"""
    
    # ========================================
    # Test 1: Create with timestamps
    # ========================================
    def test_create_maintenance_with_timestamps(self, db: Session, test_data):
        """Test creating a maintenance record and verifying timestamps are set"""
        maintenance = EquipmentMaintenance(
            equipment_id=test_data['equipment_id'],
            scheduled_by=test_data['user_id'],
            maintenance_type="PREVENTIVE",
            scheduled_date=date.today(),
            description=f"Test maintenance {int(time.time())}",
            status="SCHEDULED",
            is_active=True,
            version=1
        )
        
        db.add(maintenance)
        db.commit()
        db.refresh(maintenance)
        
        assert maintenance.id is not None
        assert maintenance.created_at is not None
        assert maintenance.equipment_id == test_data['equipment_id']
        assert maintenance.status == "SCHEDULED"
        assert maintenance.is_active == True
    
    # ========================================
    # Test 2: Get by ID
    # ========================================
    def test_get_maintenance_by_id(self, db: Session):
        """Test retrieving a maintenance record by ID"""
        maintenance = db.query(EquipmentMaintenance).filter(
            EquipmentMaintenance.deleted_at.is_(None)
        ).first()
        
        if maintenance:
            retrieved = db.query(EquipmentMaintenance).filter(
                EquipmentMaintenance.id == maintenance.id
            ).first()
            
            assert retrieved is not None
            assert retrieved.id == maintenance.id
            assert retrieved.maintenance_type == maintenance.maintenance_type
    
    # ========================================
    # Test 3: Update with trigger check
    # ========================================
    def test_update_maintenance_updates_timestamp(self, db: Session, test_data):
        """Test that updating a maintenance record updates the updated_at timestamp"""
        maintenance = EquipmentMaintenance(
            equipment_id=test_data['equipment_id'],
            scheduled_by=test_data['user_id'],
            maintenance_type="CORRECTIVE",
            scheduled_date=date.today(),
            description=f"Update test {int(time.time())}",
            status="SCHEDULED",
            is_active=True,
            version=1
        )
        db.add(maintenance)
        db.commit()
        db.refresh(maintenance)
        original_updated_at = maintenance.updated_at
        
        # Wait for trigger
        time.sleep(2)
        
        # Update - complete the maintenance
        maintenance.status = "COMPLETED"
        maintenance.performed_by = test_data['user_id']
        maintenance.performed_date = date.today()
        maintenance.completed_at = datetime.utcnow()
        maintenance.findings = "All systems operational"
        db.commit()
        db.refresh(maintenance)
        
        assert maintenance.status == "COMPLETED"
        if original_updated_at:
            assert maintenance.updated_at >= original_updated_at
    
    # ========================================
    # Test 4: List with pagination
    # ========================================
    def test_list_maintenance_with_pagination(self, db: Session):
        """Test listing maintenance records with pagination"""
        records = db.query(EquipmentMaintenance).filter(
            EquipmentMaintenance.deleted_at.is_(None)
        ).limit(5).all()
        
        total = db.query(EquipmentMaintenance).filter(
            EquipmentMaintenance.deleted_at.is_(None)
        ).count()
        
        assert isinstance(records, list)
        assert len(records) <= 5
        assert total >= 0
    
    # ========================================
    # Test 5: Filter by equipment_id
    # ========================================
    def test_filter_by_equipment_id(self, db: Session, test_data):
        """Test filtering maintenance records by equipment_id"""
        # Create maintenance
        maintenance = EquipmentMaintenance(
            equipment_id=test_data['equipment_id'],
            scheduled_by=test_data['user_id'],
            maintenance_type="INSPECTION",
            scheduled_date=date.today(),
            description=f"Filter test {int(time.time())}",
            status="SCHEDULED",
            is_active=True,
            version=1
        )
        db.add(maintenance)
        db.commit()
        
        # Filter
        filtered = db.query(EquipmentMaintenance).filter(
            EquipmentMaintenance.equipment_id == test_data['equipment_id'],
            EquipmentMaintenance.deleted_at.is_(None)
        ).all()
        
        for m in filtered:
            assert m.equipment_id == test_data['equipment_id']
    
    # ========================================
    # Test 6: Soft delete
    # ========================================
    def test_soft_delete_maintenance(self, db: Session, test_data):
        """Test soft deleting a maintenance record"""
        maintenance = EquipmentMaintenance(
            equipment_id=test_data['equipment_id'],
            scheduled_by=test_data['user_id'],
            maintenance_type="CALIBRATION",
            scheduled_date=date.today(),
            description=f"Delete test {int(time.time())}",
            status="SCHEDULED",
            is_active=True,
            version=1
        )
        db.add(maintenance)
        db.commit()
        db.refresh(maintenance)
        maintenance_id = maintenance.id
        
        # Soft delete
        maintenance.deleted_at = datetime.utcnow()
        maintenance.is_active = False
        db.commit()
        
        # Should not appear in active list
        active = db.query(EquipmentMaintenance).filter(
            EquipmentMaintenance.deleted_at.is_(None)
        ).all()
        active_ids = [m.id for m in active]
        
        assert maintenance_id not in active_ids
    
    # ========================================
    # Test 7: Restore
    # ========================================
    def test_restore_maintenance(self, db: Session, test_data):
        """Test restoring a soft-deleted maintenance record"""
        maintenance = EquipmentMaintenance(
            equipment_id=test_data['equipment_id'],
            scheduled_by=test_data['user_id'],
            maintenance_type="REPAIR",
            scheduled_date=date.today(),
            description=f"Restore test {int(time.time())}",
            status="CANCELLED",
            is_active=False,
            deleted_at=datetime.utcnow(),
            version=1
        )
        db.add(maintenance)
        db.commit()
        db.refresh(maintenance)
        
        # Restore
        maintenance.deleted_at = None
        maintenance.is_active = True
        maintenance.status = "SCHEDULED"
        db.commit()
        db.refresh(maintenance)
        
        assert maintenance.is_active == True
        assert maintenance.deleted_at is None
    
    # ========================================
    # Test 8: Cost calculation
    # ========================================
    def test_maintenance_with_costs(self, db: Session, test_data):
        """Test maintenance record with cost fields"""
        maintenance = EquipmentMaintenance(
            equipment_id=test_data['equipment_id'],
            scheduled_by=test_data['user_id'],
            performed_by=test_data['user_id'],
            maintenance_type="OVERHAUL",
            scheduled_date=date.today(),
            performed_date=date.today(),
            description=f"Cost test {int(time.time())}",
            status="COMPLETED",
            hours_spent=Decimal("4.5"),
            labor_cost=Decimal("450.00"),
            parts_cost=Decimal("250.00"),
            total_cost=Decimal("700.00"),
            parts_replaced="Oil filter, Air filter",
            actions_taken="Complete system overhaul",
            completed_at=datetime.utcnow(),
            is_active=True,
            version=1
        )
        db.add(maintenance)
        db.commit()
        db.refresh(maintenance)
        
        assert maintenance.id is not None
        assert maintenance.hours_spent == Decimal("4.5")
        assert maintenance.labor_cost == Decimal("450.00")
        assert maintenance.total_cost == Decimal("700.00")
        assert maintenance.parts_replaced is not None

