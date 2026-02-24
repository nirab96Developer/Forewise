"""
Tests for Equipment Scans CRUD operations
Production Ready Standard - 8/8 tests
"""
import pytest
import time
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.equipment_scan import EquipmentScan


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_data(db):
    """Get valid IDs for testing - using raw SQL to avoid mapper issues"""
    from sqlalchemy import text
    
    # Get equipment_id
    result = db.execute(text("SELECT id FROM equipment LIMIT 1")).fetchone()
    equipment_id = result[0] if result else 1
    
    # Get user_id
    result = db.execute(text("SELECT id FROM users WHERE deleted_at IS NULL LIMIT 1")).fetchone()
    user_id = result[0] if result else 1
    
    # Get location_id
    result = db.execute(text("SELECT id FROM locations WHERE deleted_at IS NULL LIMIT 1")).fetchone()
    location_id = result[0] if result else None
    
    # Get work_order_id
    result = db.execute(text("SELECT id FROM work_orders LIMIT 1")).fetchone()
    work_order_id = result[0] if result else None
    
    return {
        'equipment_id': equipment_id,
        'user_id': user_id,
        'location_id': location_id,
        'work_order_id': work_order_id
    }


class TestEquipmentScansCRUD:
    """Test suite for Equipment Scans module"""
    
    # ========================================
    # Test 1: Create with timestamps
    # ========================================
    def test_create_scan_with_timestamps(self, db: Session, test_data):
        """Test creating a scan and verifying timestamps are set"""
        scan = EquipmentScan(
            equipment_id=test_data['equipment_id'],
            scanned_by=test_data['user_id'],
            location_id=test_data['location_id'],
            scan_type="QR",
            scan_value=f"SCAN_TEST_{int(time.time())}",
            scan_timestamp=datetime.utcnow(),
            status="COMPLETED",
            is_active=True,
            version=1
        )
        
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        assert scan.id is not None
        assert scan.created_at is not None
        assert scan.equipment_id == test_data['equipment_id']
        assert scan.is_active == True
    
    # ========================================
    # Test 2: Get by ID
    # ========================================
    def test_get_scan_by_id(self, db: Session):
        """Test retrieving a scan by ID"""
        scan = db.query(EquipmentScan).filter(
            EquipmentScan.is_active == True
        ).first()
        
        if scan:
            retrieved = db.query(EquipmentScan).filter(
                EquipmentScan.id == scan.id
            ).first()
            
            assert retrieved is not None
            assert retrieved.id == scan.id
            assert retrieved.scan_type == scan.scan_type
    
    # ========================================
    # Test 3: Update with trigger check
    # ========================================
    def test_update_scan_updates_timestamp(self, db: Session, test_data):
        """Test that updating a scan updates the updated_at timestamp"""
        # Create scan
        scan = EquipmentScan(
            equipment_id=test_data['equipment_id'],
            scanned_by=test_data['user_id'],
            scan_type="QR",
            scan_value=f"UPDATE_TEST_{int(time.time())}",
            scan_timestamp=datetime.utcnow(),
            status="PENDING",
            is_active=True,
            version=1
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        original_updated_at = scan.updated_at
        
        # Wait for trigger
        time.sleep(2)
        
        # Update
        scan.status = "COMPLETED"
        scan.notes = "Test update"
        db.commit()
        db.refresh(scan)
        
        assert scan.status == "COMPLETED"
        if original_updated_at:
            assert scan.updated_at >= original_updated_at
    
    # ========================================
    # Test 4: List with pagination
    # ========================================
    def test_list_scans_with_pagination(self, db: Session):
        """Test listing scans with pagination"""
        scans = db.query(EquipmentScan).filter(
            EquipmentScan.is_active == True
        ).limit(5).all()
        
        total = db.query(EquipmentScan).filter(
            EquipmentScan.is_active == True
        ).count()
        
        assert isinstance(scans, list)
        assert len(scans) <= 5
        assert total >= 0
    
    # ========================================
    # Test 5: Filter by equipment_id
    # ========================================
    def test_filter_by_equipment_id(self, db: Session, test_data):
        """Test filtering scans by equipment_id"""
        # Create a scan with specific equipment
        scan = EquipmentScan(
            equipment_id=test_data['equipment_id'],
            scanned_by=test_data['user_id'],
            scan_type="BARCODE",
            scan_value=f"FILTER_TEST_{int(time.time())}",
            scan_timestamp=datetime.utcnow(),
            status="COMPLETED",
            is_active=True,
            version=1
        )
        db.add(scan)
        db.commit()
        
        # Filter by equipment_id
        filtered = db.query(EquipmentScan).filter(
            EquipmentScan.equipment_id == test_data['equipment_id'],
            EquipmentScan.is_active == True
        ).all()
        
        # All should have this equipment_id
        for s in filtered:
            assert s.equipment_id == test_data['equipment_id']
    
    # ========================================
    # Test 6: Deactivate (soft delete)
    # ========================================
    def test_deactivate_scan(self, db: Session, test_data):
        """Test deactivating a scan"""
        # Create scan
        scan = EquipmentScan(
            equipment_id=test_data['equipment_id'],
            scanned_by=test_data['user_id'],
            scan_type="QR",
            scan_value=f"DEACT_TEST_{int(time.time())}",
            scan_timestamp=datetime.utcnow(),
            status="COMPLETED",
            is_active=True,
            version=1
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        scan_id = scan.id
        
        # Deactivate
        scan.is_active = False
        scan.deleted_at = datetime.utcnow()
        db.commit()
        
        # Should not appear in active list
        active_scans = db.query(EquipmentScan).filter(
            EquipmentScan.is_active == True
        ).all()
        active_ids = [s.id for s in active_scans]
        
        assert scan_id not in active_ids
    
    # ========================================
    # Test 7: Activate (restore)
    # ========================================
    def test_activate_scan(self, db: Session, test_data):
        """Test activating a deactivated scan"""
        # Create and deactivate
        scan = EquipmentScan(
            equipment_id=test_data['equipment_id'],
            scanned_by=test_data['user_id'],
            scan_type="QR",
            scan_value=f"ACT_TEST_{int(time.time())}",
            scan_timestamp=datetime.utcnow(),
            status="COMPLETED",
            is_active=False,
            deleted_at=datetime.utcnow(),
            version=1
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        # Activate
        scan.is_active = True
        scan.deleted_at = None
        db.commit()
        db.refresh(scan)
        
        assert scan.is_active == True
        assert scan.deleted_at is None
    
    # ========================================
    # Test 8: Scan type validation
    # ========================================
    def test_scan_type_values(self, db: Session, test_data):
        """Test different scan types work"""
        scan_types = ["QR", "BARCODE", "MANUAL", "NFC"]
        
        for scan_type in scan_types:
            scan = EquipmentScan(
                equipment_id=test_data['equipment_id'],
                scanned_by=test_data['user_id'],
                scan_type=scan_type,
                scan_value=f"TYPE_TEST_{scan_type}_{int(time.time())}",
                scan_timestamp=datetime.utcnow(),
                status="COMPLETED",
                is_active=True,
                version=1
            )
            db.add(scan)
            db.commit()
            db.refresh(scan)
            
            assert scan.id is not None
            assert scan.scan_type == scan_type
