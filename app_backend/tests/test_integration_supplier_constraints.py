"""
Integration Tests for Supplier Constraints Flow
Work Order → Supplier Constraint Log (with reasons)

Tests the complete supplier constraint lifecycle.
"""
import pytest
import time
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import SessionLocal
from app.models.supplier_constraint_log import SupplierConstraintLog
from app.models.supplier_constraint_reason import SupplierConstraintReason


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_data(db):
    """Get valid IDs for testing"""
    result = db.execute(text("SELECT id FROM work_orders LIMIT 1")).fetchone()
    work_order_id = result[0] if result else 1
    
    result = db.execute(text("SELECT id FROM suppliers WHERE deleted_at IS NULL LIMIT 2")).fetchall()
    supplier_ids = [r[0] for r in result] if result else [1]
    
    result = db.execute(text("SELECT id FROM supplier_constraint_reasons WHERE is_active = true LIMIT 1")).fetchone()
    reason_id = result[0] if result else None
    
    result = db.execute(text("SELECT id FROM users WHERE deleted_at IS NULL LIMIT 2")).fetchall()
    user_ids = [r[0] for r in result] if result else [1]
    
    return {
        'work_order_id': work_order_id,
        'supplier_ids': supplier_ids,
        'reason_id': reason_id,
        'user_ids': user_ids
    }


class TestSupplierConstraintsIntegration:
    """Integration tests for supplier constraint workflow"""
    
    # ========================================
    # Test 1: Create Constraint with Reason
    # ========================================
    def test_create_constraint_with_reason(self, db: Session, test_data):
        """Test creating a supplier constraint with a predefined reason"""
        log = SupplierConstraintLog(
            work_order_id=test_data['work_order_id'],
            supplier_id=test_data['supplier_ids'][0],
            constraint_reason_id=test_data['reason_id'],
            constraint_reason_text=f"Constraint with reason {int(time.time())}",
            justification="Supplier is at full capacity",
            created_by=test_data['user_ids'][0]
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        assert log.id is not None
        assert log.constraint_reason_id == test_data['reason_id']
        assert log.created_at is not None
    
    # ========================================
    # Test 2: Create Constraint without Reason
    # ========================================
    def test_create_constraint_without_predefined_reason(self, db: Session, test_data):
        """Test creating a constraint with custom text only"""
        log = SupplierConstraintLog(
            work_order_id=test_data['work_order_id'],
            supplier_id=test_data['supplier_ids'][0],
            constraint_reason_id=None,  # No predefined reason
            constraint_reason_text="Custom constraint: Equipment not compatible",
            justification="Special equipment requirements not met",
            created_by=test_data['user_ids'][0]
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        assert log.id is not None
        assert log.constraint_reason_id is None
        assert "Equipment not compatible" in log.constraint_reason_text
    
    # ========================================
    # Test 3: Approve Constraint
    # ========================================
    def test_approve_constraint(self, db: Session, test_data):
        """Test approving a supplier constraint"""
        # Arrange
        log = SupplierConstraintLog(
            work_order_id=test_data['work_order_id'],
            supplier_id=test_data['supplier_ids'][0],
            constraint_reason_text=f"Approval test {int(time.time())}",
            justification="Pending approval",
            created_by=test_data['user_ids'][0]
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        # Act: Approve by different user (if available)
        approver_id = test_data['user_ids'][1] if len(test_data['user_ids']) > 1 else test_data['user_ids'][0]
        log.approved_by = approver_id
        log.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(log)
        
        # Assert
        assert log.approved_by is not None
        assert log.approved_at is not None
    
    # ========================================
    # Test 4: Multiple Constraints per Work Order
    # ========================================
    def test_multiple_constraints_per_work_order(self, db: Session, test_data):
        """Test adding multiple supplier constraints to same work order"""
        constraints = []
        timestamp = int(time.time())
        
        # Create constraints for different suppliers
        for i, supplier_id in enumerate(test_data['supplier_ids']):
            log = SupplierConstraintLog(
                work_order_id=test_data['work_order_id'],
                supplier_id=supplier_id,
                constraint_reason_text=f"Multi-constraint test {timestamp}-{i}",
                justification=f"Reason for supplier {supplier_id}",
                created_by=test_data['user_ids'][0]
            )
            db.add(log)
            constraints.append(log)
        
        db.commit()
        
        # Verify all were created
        for c in constraints:
            db.refresh(c)
            assert c.id is not None
        
        # Query constraints for work order
        match_prefix = f"Multi-constraint test {timestamp}-"
        work_order_constraints = db.query(SupplierConstraintLog).filter(
            SupplierConstraintLog.work_order_id == test_data['work_order_id'],
            SupplierConstraintLog.constraint_reason_text.like(f"{match_prefix}%")
        ).all()
        
        assert len(work_order_constraints) == len(test_data['supplier_ids'])
    
    # ========================================
    # Test 5: Constraint History for Supplier
    # ========================================
    def test_constraint_history_for_supplier(self, db: Session, test_data):
        """Test viewing constraint history for a specific supplier"""
        timestamp = int(time.time())
        supplier_id = test_data['supplier_ids'][0]
        
        # Create multiple constraints for same supplier (on different work orders or dates)
        for i in range(3):
            log = SupplierConstraintLog(
                work_order_id=test_data['work_order_id'],
                supplier_id=supplier_id,
                constraint_reason_text=f"History test {timestamp}-{i}",
                justification=f"Historical constraint {i+1}",
                created_by=test_data['user_ids'][0]
            )
            db.add(log)
        db.commit()
        
        # Query history
        history = db.query(SupplierConstraintLog).filter(
            SupplierConstraintLog.supplier_id == supplier_id,
            SupplierConstraintLog.constraint_reason_text.like(f"%{timestamp}%")
        ).order_by(SupplierConstraintLog.created_at.desc()).all()
        
        assert len(history) >= 3
    
    # ========================================
    # Test 6: Constraints with Approval Workflow
    # ========================================
    def test_full_approval_workflow(self, db: Session, test_data):
        """Test complete constraint workflow: Create → Justify → Approve"""
        # Step 1: Create
        log = SupplierConstraintLog(
            work_order_id=test_data['work_order_id'],
            supplier_id=test_data['supplier_ids'][0],
            constraint_reason_id=test_data['reason_id'],
            constraint_reason_text=f"Workflow test {int(time.time())}",
            created_by=test_data['user_ids'][0]
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        # Step 2: Add justification
        log.justification = "After review, supplier capacity confirmed to be limited"
        db.commit()
        
        # Step 3: Approve
        approver_id = test_data['user_ids'][1] if len(test_data['user_ids']) > 1 else test_data['user_ids'][0]
        log.approved_by = approver_id
        log.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(log)
        
        # Assert complete workflow
        assert log.constraint_reason_text is not None
        assert log.justification is not None
        assert log.approved_by is not None
        assert log.approved_at is not None
    
    # ========================================
    # Test 7: Filter Constraints by Reason
    # ========================================
    def test_filter_by_constraint_reason(self, db: Session, test_data):
        """Test filtering constraints by reason type"""
        if test_data['reason_id']:
            # Create constraint with specific reason
            log = SupplierConstraintLog(
                work_order_id=test_data['work_order_id'],
                supplier_id=test_data['supplier_ids'][0],
                constraint_reason_id=test_data['reason_id'],
                constraint_reason_text=f"Reason filter test {int(time.time())}",
                created_by=test_data['user_ids'][0]
            )
            db.add(log)
            db.commit()
            
            # Filter by reason
            filtered = db.query(SupplierConstraintLog).filter(
                SupplierConstraintLog.constraint_reason_id == test_data['reason_id']
            ).all()
            
            assert len(filtered) >= 1
            for f in filtered:
                assert f.constraint_reason_id == test_data['reason_id']
    
    # ========================================
    # Test 8: Constraint Reasons Statistics
    # ========================================
    def test_constraint_reasons_usage(self, db: Session, test_data):
        """Test analyzing constraint reason usage patterns"""
        # Get count by reason
        from sqlalchemy import func
        
        stats = db.query(
            SupplierConstraintLog.constraint_reason_id,
            func.count(SupplierConstraintLog.id).label('count')
        ).group_by(
            SupplierConstraintLog.constraint_reason_id
        ).all()
        
        # Should return at least empty results
        assert isinstance(stats, list)
        
        # Verify approved vs pending
        approved_count = db.query(func.count(SupplierConstraintLog.id)).filter(
            SupplierConstraintLog.approved_at.isnot(None)
        ).scalar()
        
        pending_count = db.query(func.count(SupplierConstraintLog.id)).filter(
            SupplierConstraintLog.approved_at.is_(None)
        ).scalar()
        
        assert approved_count >= 0
        assert pending_count >= 0


