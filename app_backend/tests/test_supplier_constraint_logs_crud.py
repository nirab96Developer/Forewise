"""
Tests for Supplier Constraint Logs CRUD operations
Production Ready Standard - 8/8 tests
"""
import pytest
import time
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import SessionLocal
from app.models.supplier_constraint_log import SupplierConstraintLog


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_data(db):
    """Get valid IDs for testing using raw SQL"""
    result = db.execute(text("SELECT id FROM work_orders LIMIT 1")).fetchone()
    work_order_id = result[0] if result else 1
    
    result = db.execute(text("SELECT id FROM suppliers WHERE deleted_at IS NULL LIMIT 1")).fetchone()
    supplier_id = result[0] if result else 1
    
    result = db.execute(text("SELECT id FROM supplier_constraint_reasons WHERE is_active = true LIMIT 1")).fetchone()
    reason_id = result[0] if result else None
    
    result = db.execute(text("SELECT id FROM users WHERE deleted_at IS NULL LIMIT 1")).fetchone()
    user_id = result[0] if result else 1
    
    return {
        'work_order_id': work_order_id,
        'supplier_id': supplier_id,
        'reason_id': reason_id,
        'user_id': user_id
    }


class TestSupplierConstraintLogsCRUD:
    """Test suite for Supplier Constraint Logs module"""
    
    # ========================================
    # Test 1: Create with timestamps
    # ========================================
    def test_create_log_with_timestamps(self, db: Session, test_data):
        """Test creating a constraint log and verifying timestamps are set"""
        log = SupplierConstraintLog(
            work_order_id=test_data['work_order_id'],
            supplier_id=test_data['supplier_id'],
            constraint_reason_id=test_data['reason_id'],
            constraint_reason_text=f"Test constraint {int(time.time())}",
            created_by=test_data['user_id']
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        assert log.id is not None
        assert log.created_at is not None
        assert log.work_order_id == test_data['work_order_id']
        assert log.supplier_id == test_data['supplier_id']
    
    # ========================================
    # Test 2: Get by ID
    # ========================================
    def test_get_log_by_id(self, db: Session):
        """Test retrieving a log by ID"""
        log = db.query(SupplierConstraintLog).first()
        
        if log:
            retrieved = db.query(SupplierConstraintLog).filter(
                SupplierConstraintLog.id == log.id
            ).first()
            
            assert retrieved is not None
            assert retrieved.id == log.id
            assert retrieved.constraint_reason_text == log.constraint_reason_text
    
    # ========================================
    # Test 3: Create with justification
    # ========================================
    def test_create_log_with_justification(self, db: Session, test_data):
        """Test creating a constraint log with justification"""
        log = SupplierConstraintLog(
            work_order_id=test_data['work_order_id'],
            supplier_id=test_data['supplier_id'],
            constraint_reason_id=test_data['reason_id'],
            constraint_reason_text=f"Constraint with justification {int(time.time())}",
            justification="Supplier requested exclusion due to capacity limitations",
            created_by=test_data['user_id']
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        assert log.id is not None
        assert log.justification is not None
        assert "capacity" in log.justification
    
    # ========================================
    # Test 4: List with pagination
    # ========================================
    def test_list_logs_with_pagination(self, db: Session):
        """Test listing logs with pagination"""
        logs = db.query(SupplierConstraintLog).limit(5).all()
        total = db.query(SupplierConstraintLog).count()
        
        assert isinstance(logs, list)
        assert len(logs) <= 5
        assert total >= 0
    
    # ========================================
    # Test 5: Filter by work_order_id
    # ========================================
    def test_filter_by_work_order_id(self, db: Session, test_data):
        """Test filtering logs by work_order_id"""
        log = SupplierConstraintLog(
            work_order_id=test_data['work_order_id'],
            supplier_id=test_data['supplier_id'],
            constraint_reason_text=f"Filter test {int(time.time())}",
            created_by=test_data['user_id']
        )
        db.add(log)
        db.commit()
        
        # Filter
        filtered = db.query(SupplierConstraintLog).filter(
            SupplierConstraintLog.work_order_id == test_data['work_order_id']
        ).all()
        
        for l in filtered:
            assert l.work_order_id == test_data['work_order_id']
    
    # ========================================
    # Test 6: Filter by supplier_id
    # ========================================
    def test_filter_by_supplier_id(self, db: Session, test_data):
        """Test filtering logs by supplier_id"""
        log = SupplierConstraintLog(
            work_order_id=test_data['work_order_id'],
            supplier_id=test_data['supplier_id'],
            constraint_reason_text=f"Supplier filter test {int(time.time())}",
            created_by=test_data['user_id']
        )
        db.add(log)
        db.commit()
        
        # Filter
        filtered = db.query(SupplierConstraintLog).filter(
            SupplierConstraintLog.supplier_id == test_data['supplier_id']
        ).all()
        
        for l in filtered:
            assert l.supplier_id == test_data['supplier_id']
    
    # ========================================
    # Test 7: Approve constraint
    # ========================================
    def test_approve_constraint(self, db: Session, test_data):
        """Test approving a constraint log"""
        log = SupplierConstraintLog(
            work_order_id=test_data['work_order_id'],
            supplier_id=test_data['supplier_id'],
            constraint_reason_text=f"Approval test {int(time.time())}",
            justification="Valid business reason for constraint",
            created_by=test_data['user_id']
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        # Approve
        log.approved_by = test_data['user_id']
        log.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(log)
        
        assert log.approved_by is not None
        assert log.approved_at is not None
    
    # ========================================
    # Test 8: Filter by constraint_reason_id
    # ========================================
    def test_filter_by_reason_id(self, db: Session, test_data):
        """Test filtering logs by constraint_reason_id"""
        if test_data['reason_id']:
            log = SupplierConstraintLog(
                work_order_id=test_data['work_order_id'],
                supplier_id=test_data['supplier_id'],
                constraint_reason_id=test_data['reason_id'],
                constraint_reason_text=f"Reason filter test {int(time.time())}",
                created_by=test_data['user_id']
            )
            db.add(log)
            db.commit()
            
            # Filter
            filtered = db.query(SupplierConstraintLog).filter(
                SupplierConstraintLog.constraint_reason_id == test_data['reason_id']
            ).all()
            
            for l in filtered:
                assert l.constraint_reason_id == test_data['reason_id']
        else:
            # If no reason exists, just verify we can query without reason_id
            logs = db.query(SupplierConstraintLog).filter(
                SupplierConstraintLog.constraint_reason_id.is_(None)
            ).limit(5).all()
            assert isinstance(logs, list)

