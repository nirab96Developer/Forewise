"""
Tests for budget financial integrity.
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from app.services.budget_service import _sync_remaining, _assert_invariants


def _mock_budget(total=10000, committed=3000, spent=2000, remaining=None):
    b = MagicMock()
    b.id = 1
    b.total_amount = Decimal(str(total))
    b.committed_amount = Decimal(str(committed))
    b.spent_amount = Decimal(str(spent))
    b.remaining_amount = Decimal(str(remaining)) if remaining is not None else None
    return b


class TestSyncRemaining:

    def test_basic_calculation(self):
        b = _mock_budget(10000, 3000, 2000)
        _sync_remaining(b)
        assert b.remaining_amount == Decimal("5000")

    def test_floor_at_zero(self):
        b = _mock_budget(10000, 6000, 5000)
        _sync_remaining(b)
        assert b.remaining_amount == Decimal("0")

    def test_zero_budget(self):
        b = _mock_budget(0, 0, 0)
        _sync_remaining(b)
        assert b.remaining_amount == Decimal("0")

    def test_full_spend(self):
        b = _mock_budget(10000, 0, 10000)
        _sync_remaining(b)
        assert b.remaining_amount == Decimal("0")

    def test_partial_commit_partial_spend(self):
        b = _mock_budget(10000, 1500, 3500)
        _sync_remaining(b)
        assert b.remaining_amount == Decimal("5000")

    def test_none_fields_treated_as_zero(self):
        b = _mock_budget(10000, 0, 0)
        b.committed_amount = None
        b.spent_amount = None
        _sync_remaining(b)
        assert b.remaining_amount == Decimal("10000")


class TestAssertInvariants:

    def test_healthy_budget_passes(self):
        b = _mock_budget(10000, 3000, 2000, 5000)
        _assert_invariants(b, "test")

    @pytest.fixture(autouse=False)
    def _force_production(self, monkeypatch):
        from app.core.config import settings
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    def test_negative_committed_raises_in_production(self, monkeypatch):
        from app.core.config import settings
        from app.core.exceptions import BusinessException
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")
        b = _mock_budget(10000, -100, 0, 10100)
        with pytest.raises(BusinessException, match="committed_amount < 0"):
            _assert_invariants(b, "test")

    def test_overflow_raises_in_production(self, monkeypatch):
        from app.core.config import settings
        from app.core.exceptions import BusinessException
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")
        b = _mock_budget(10000, 6000, 5000, -1000)
        with pytest.raises(BusinessException, match="exceeds total"):
            _assert_invariants(b, "test")

    def test_negative_remaining_raises_in_production(self, monkeypatch):
        from app.core.config import settings
        from app.core.exceptions import BusinessException
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")
        b = _mock_budget(10000, 0, 0, -500)
        with pytest.raises(BusinessException, match="remaining_amount < 0"):
            _assert_invariants(b, "test")

    def test_violations_only_warn_in_development(self, monkeypatch, caplog):
        import logging
        from app.core.config import settings
        monkeypatch.setattr(settings, "ENVIRONMENT", "development")
        with caplog.at_level(logging.WARNING, logger="budget"):
            b = _mock_budget(10000, -100, 0, 10100)
            _assert_invariants(b, "test")
        assert "committed_amount < 0" in caplog.text


class TestFreezeValidation:

    def test_freeze_rejects_insufficient(self):
        from app.services.budget_service import freeze_budget_for_work_order
        db = MagicMock()
        budget = _mock_budget(10000, 5000, 4000, 1000)
        db.query.return_value.filter.return_value.first.return_value = budget

        with pytest.raises(ValueError, match="אין מספיק"):
            freeze_budget_for_work_order(1, 1, 2000, db)


class TestReleaseLogic:

    def test_release_zeros_wo_frozen(self):
        from app.services.budget_service import release_budget_freeze
        db = MagicMock()
        wo = MagicMock()
        wo.id = 1
        wo.project_id = 1
        wo.frozen_amount = Decimal("5000")
        wo.remaining_frozen = Decimal("5000")

        budget = _mock_budget(10000, 5000, 2000, 3000)

        def query_side_effect(model):
            m = MagicMock()
            if model.__name__ == "WorkOrder":
                m.filter.return_value.first.return_value = wo
            else:
                m.filter.return_value.first.return_value = budget
            return m

        db.query.side_effect = query_side_effect
        release_budget_freeze(1, 0, db)

        assert wo.frozen_amount == Decimal(0)
        assert wo.remaining_frozen == Decimal(0)
