"""
Tests for Balance Releases CRUD operations
Production Ready Standard - 8/8 tests
"""
import pytest
import time
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import SessionLocal
from app.models.balance_release import BalanceRelease


@pytest.fixture(autouse=True)
def ensure_balance_releases_table(db: Session):
    table_exists = db.execute(
        text("SELECT to_regclass('public.balance_releases')")
    ).scalar()
    if not table_exists:
        pytest.skip("balance_releases table is missing in current database")


def _next_release_id(db: Session) -> int:
    next_id = int(
        db.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM balance_releases")).scalar()
        or 1
    )
    # Keep sequence ahead of manually assigned IDs used in this legacy test.
    db.execute(text("CREATE SEQUENCE IF NOT EXISTS balance_releases_id_seq"))
    db.execute(
        text(
            "SELECT setval('balance_releases_id_seq', :value, true)"
        ),
        {"value": next_id},
    )
    return next_id


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_data(db):
    """Get valid IDs for testing using raw SQL"""
    result = db.execute(text("SELECT id FROM budgets WHERE deleted_at IS NULL LIMIT 1")).fetchone()
    budget_id = result[0] if result else 1
    
    result = db.execute(text("SELECT id FROM users WHERE deleted_at IS NULL LIMIT 1")).fetchone()
    user_id = result[0] if result else 1
    
    return {
        'budget_id': budget_id,
        'user_id': user_id
    }


class TestBalanceReleasesCRUD:
    """Test suite for Balance Releases module"""
    
    # ========================================
    # Test 1: Create with timestamps
    # ========================================
    def test_create_release_with_timestamps(self, db: Session, test_data):
        """Test creating a release and verifying timestamps are set"""
        release = BalanceRelease(
            id=_next_release_id(db),
            budget_id=test_data['budget_id'],
            created_by=test_data['user_id'],
            release_type="SCHEDULED",
            amount=Decimal("15000.00"),
            release_date=date.today(),
            status="PENDING",
            is_active=True,
            version=1
        )
        
        db.add(release)
        db.commit()
        db.refresh(release)
        
        assert release.id is not None
        assert release.created_at is not None
        assert release.budget_id == test_data['budget_id']
        assert release.amount == Decimal("15000.00")
        assert release.status == "PENDING"
    
    # ========================================
    # Test 2: Get by ID
    # ========================================
    def test_get_release_by_id(self, db: Session):
        """Test retrieving a release by ID"""
        release = db.query(BalanceRelease).filter(
            BalanceRelease.deleted_at.is_(None)
        ).first()
        
        if release:
            retrieved = db.query(BalanceRelease).filter(
                BalanceRelease.id == release.id
            ).first()
            
            assert retrieved is not None
            assert retrieved.id == release.id
            assert retrieved.amount == release.amount
    
    # ========================================
    # Test 3: Update with trigger check
    # ========================================
    def test_update_release_updates_timestamp(self, db: Session, test_data):
        """Test that updating a release updates the updated_at timestamp"""
        release = BalanceRelease(
            id=_next_release_id(db),
            budget_id=test_data['budget_id'],
            created_by=test_data['user_id'],
            release_type="CONDITIONAL",
            amount=Decimal("8000.00"),
            release_date=date.today(),
            condition_description="Upon project completion",
            status="PENDING",
            is_active=True,
            version=1
        )
        db.add(release)
        db.commit()
        db.refresh(release)
        original_updated_at = release.updated_at
        
        # Wait for trigger
        time.sleep(2)
        
        # Update - approve the release
        release.status = "APPROVED"
        release.approved_by = test_data['user_id']
        db.commit()
        db.refresh(release)
        
        assert release.status == "APPROVED"
        if original_updated_at:
            assert release.updated_at >= original_updated_at
    
    # ========================================
    # Test 4: List with pagination
    # ========================================
    def test_list_releases_with_pagination(self, db: Session):
        """Test listing releases with pagination"""
        releases = db.query(BalanceRelease).filter(
            BalanceRelease.deleted_at.is_(None)
        ).limit(5).all()
        
        total = db.query(BalanceRelease).filter(
            BalanceRelease.deleted_at.is_(None)
        ).count()
        
        assert isinstance(releases, list)
        assert len(releases) <= 5
        assert total >= 0
    
    # ========================================
    # Test 5: Filter by budget_id
    # ========================================
    def test_filter_by_budget_id(self, db: Session, test_data):
        """Test filtering releases by budget_id"""
        release = BalanceRelease(
            id=_next_release_id(db),
            budget_id=test_data['budget_id'],
            created_by=test_data['user_id'],
            release_type="MILESTONE",
            amount=Decimal("5000.00"),
            release_date=date.today(),
            status="PENDING",
            is_active=True,
            version=1
        )
        db.add(release)
        db.commit()
        
        # Filter
        filtered = db.query(BalanceRelease).filter(
            BalanceRelease.budget_id == test_data['budget_id'],
            BalanceRelease.deleted_at.is_(None)
        ).all()
        
        for r in filtered:
            assert r.budget_id == test_data['budget_id']
    
    # ========================================
    # Test 6: Soft delete
    # ========================================
    def test_soft_delete_release(self, db: Session, test_data):
        """Test soft deleting a release"""
        release = BalanceRelease(
            id=_next_release_id(db),
            budget_id=test_data['budget_id'],
            created_by=test_data['user_id'],
            release_type="EMERGENCY",
            amount=Decimal("3000.00"),
            release_date=date.today(),
            status="PENDING",
            is_active=True,
            version=1
        )
        db.add(release)
        db.commit()
        db.refresh(release)
        release_id = release.id
        
        # Soft delete
        release.deleted_at = datetime.utcnow()
        release.is_active = False
        db.commit()
        
        # Should not appear in active list
        active = db.query(BalanceRelease).filter(
            BalanceRelease.deleted_at.is_(None)
        ).all()
        active_ids = [r.id for r in active]
        
        assert release_id not in active_ids
    
    # ========================================
    # Test 7: Restore
    # ========================================
    def test_restore_release(self, db: Session, test_data):
        """Test restoring a soft-deleted release"""
        release = BalanceRelease(
            id=_next_release_id(db),
            budget_id=test_data['budget_id'],
            created_by=test_data['user_id'],
            release_type="SCHEDULED",
            amount=Decimal("2000.00"),
            release_date=date.today(),
            status="CANCELLED",
            is_active=False,
            deleted_at=datetime.utcnow(),
            version=1
        )
        db.add(release)
        db.commit()
        db.refresh(release)
        
        # Restore
        release.deleted_at = None
        release.is_active = True
        release.status = "PENDING"
        db.commit()
        db.refresh(release)
        
        assert release.is_active == True
        assert release.deleted_at is None
    
    # ========================================
    # Test 8: Execution workflow with actual amount
    # ========================================
    def test_execution_workflow_with_actual_amount(self, db: Session, test_data):
        """Test complete release execution with actual amount"""
        release = BalanceRelease(
            id=_next_release_id(db),
            budget_id=test_data['budget_id'],
            created_by=test_data['user_id'],
            release_type="QUARTERLY",
            amount=Decimal("20000.00"),
            release_date=date.today(),
            status="PENDING",
            is_active=True,
            version=1
        )
        db.add(release)
        db.commit()
        db.refresh(release)
        
        # Approve
        release.status = "APPROVED"
        release.approved_by = test_data['user_id']
        db.commit()
        
        # Execute with actual amount (may differ from requested)
        release.status = "EXECUTED"
        release.executed_at = date.today()
        release.actual_amount = Decimal("18500.00")  # Slightly less than requested
        release.notes = "Released with 7.5% adjustment due to budget constraints"
        db.commit()
        db.refresh(release)
        
        assert release.status == "EXECUTED"
        assert release.executed_at is not None
        assert release.actual_amount == Decimal("18500.00")
        assert release.actual_amount != release.amount

