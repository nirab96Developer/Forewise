"""
Tests for permission enforcement on /api/v1/pricing/{simulate-days,reports/*}.

Phase 2 Wave 7.H — three sensitive financial endpoints used to accept
any authenticated user (including SUPPLIER) and return supplier rates,
hourly costs, project totals. Now require `budgets.read` (assigned in
DB to ADMIN, ACCOUNTANT, REGION_MANAGER, AREA_MANAGER, WORK_MANAGER —
NOT SUPPLIER).

Endpoints:
  GET /pricing/simulate-days
  GET /pricing/reports/by-project
  GET /pricing/reports/by-supplier

The existing GET /pricing/reports/by-equipment-type stays unchanged
for now — it's already in the matrix as 🟢 (had inline auth check
patterns; out of scope for 7.H).
"""
import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.pricing import (
    get_pricing_report_by_project,
    get_pricing_report_by_supplier,
    simulate_days_cost,
)


def _user(role_code: str, *, perms: set[str] | None = None):
    user = MagicMock()
    user.id = 1
    user.role_id = 1
    user.is_active = True
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = [MagicMock(code=p) for p in (perms or set())]
    user._permissions = set(perms or set())
    return user


def _admin():
    return _user("ADMIN")


def _accountant():
    return _user("ACCOUNTANT", perms={"budgets.read", "invoices.read"})


def _supplier():
    return _user("SUPPLIER", perms={"equipment.read"})


def _work_manager_no_perm():
    return _user("WORK_MANAGER", perms={"work_orders.read"})


class _DBStub:
    """Minimal session — pricing handlers do query().filter().group_by()
    chains plus rate_service calls. We mock those service calls separately."""

    def query(self, *a, **kw):
        return self

    def filter(self, *a, **kw):
        return self

    def group_by(self, *a, **kw):
        return self

    def order_by(self, *a, **kw):
        return self

    def offset(self, *a, **kw):
        return self

    def limit(self, *a, **kw):
        return self

    def join(self, *a, **kw):
        return self

    def outerjoin(self, *a, **kw):
        return self

    def having(self, *a, **kw):
        return self

    def count(self):
        return 0

    def all(self):
        return []

    def first(self):
        return None

    def execute(self, *a, **kw):
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = None
        return cursor


# ===========================================================================
# simulate_days_cost
# ===========================================================================

class TestSimulateDays:

    def test_admin_passes(self, monkeypatch):
        # Stub the rate_service so simulate doesn't hit a real DB.
        from app.routers import pricing as pricing_mod
        fake_service = MagicMock()
        fake_service.compute_worklog_cost.return_value = {
            "hourly_rate": 100.0,
            "total_cost": 4500.0,
            "total_cost_with_vat": 5310.0,
            "rate_source": "system_rate",
            "rate_source_name": "system",
        }
        monkeypatch.setattr(pricing_mod, "get_rate_service", lambda db: fake_service)

        result = asyncio.run(simulate_days_cost(
            equipment_type_id=5, days=5, hours_per_day=8,
            supplier_id=None, project_id=None,
            db=_DBStub(), current_user=_admin(),
        ))
        assert result is not None

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(simulate_days_cost(
                equipment_type_id=5, days=5, hours_per_day=8,
                supplier_id=None, project_id=None,
                db=_DBStub(), current_user=_supplier(),
            ))
        assert exc.value.status_code == 403

    def test_work_manager_without_budgets_read_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(simulate_days_cost(
                equipment_type_id=5, days=5, hours_per_day=8,
                supplier_id=None, project_id=None,
                db=_DBStub(), current_user=_work_manager_no_perm(),
            ))
        assert exc.value.status_code == 403

    def test_accountant_with_budgets_read_passes(self, monkeypatch):
        from app.routers import pricing as pricing_mod
        fake_service = MagicMock()
        fake_service.compute_worklog_cost.return_value = {
            "hourly_rate": 100.0,
            "total_cost": 4500.0,
            "total_cost_with_vat": 5310.0,
            "rate_source": "system_rate",
            "rate_source_name": "system",
        }
        monkeypatch.setattr(pricing_mod, "get_rate_service", lambda db: fake_service)
        result = asyncio.run(simulate_days_cost(
            equipment_type_id=5, days=5, hours_per_day=8,
            supplier_id=None, project_id=None,
            db=_DBStub(), current_user=_accountant(),
        ))
        assert result is not None


# ===========================================================================
# get_pricing_report_by_project
# ===========================================================================

class TestReportByProject:

    def test_admin_passes(self):
        result = asyncio.run(get_pricing_report_by_project(
            date_from=None, date_to=None, supplier_id=None, status=None,
            page=1, page_size=50,
            db=_DBStub(), current_user=_admin(),
        ))
        assert result is not None

    def test_accountant_with_budgets_read_passes(self):
        result = asyncio.run(get_pricing_report_by_project(
            date_from=None, date_to=None, supplier_id=None, status=None,
            page=1, page_size=50,
            db=_DBStub(), current_user=_accountant(),
        ))
        assert result is not None

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_pricing_report_by_project(
                date_from=None, date_to=None, supplier_id=None, status=None,
                page=1, page_size=50,
                db=_DBStub(), current_user=_supplier(),
            ))
        assert exc.value.status_code == 403

    def test_work_manager_without_budgets_read_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_pricing_report_by_project(
                date_from=None, date_to=None, supplier_id=None, status=None,
                page=1, page_size=50,
                db=_DBStub(), current_user=_work_manager_no_perm(),
            ))
        assert exc.value.status_code == 403


# ===========================================================================
# get_pricing_report_by_supplier
# ===========================================================================

class TestReportBySupplier:

    def test_admin_passes(self):
        result = asyncio.run(get_pricing_report_by_supplier(
            date_from=None, date_to=None, project_id=None, status=None,
            page=1, page_size=50,
            db=_DBStub(), current_user=_admin(),
        ))
        assert result is not None

    def test_accountant_with_budgets_read_passes(self):
        result = asyncio.run(get_pricing_report_by_supplier(
            date_from=None, date_to=None, project_id=None, status=None,
            page=1, page_size=50,
            db=_DBStub(), current_user=_accountant(),
        ))
        assert result is not None

    def test_supplier_blocked_403(self):
        """Critical: supplier must NOT see other suppliers' rates."""
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_pricing_report_by_supplier(
                date_from=None, date_to=None, project_id=None, status=None,
                page=1, page_size=50,
                db=_DBStub(), current_user=_supplier(),
            ))
        assert exc.value.status_code == 403
