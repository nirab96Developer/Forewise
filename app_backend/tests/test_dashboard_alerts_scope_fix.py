"""
Phase 3 Wave 2.2.c — fix the SQL scope bug in /dashboard/alerts.

Background
----------
PHASE3_WAVE22_RECON.md flagged this code:

    overbudget_query = db.query(Budget).filter(...)
    if role == "REGION_MANAGER":
        overbudget_query = overbudget_query.filter(
            Project.region_id == current_user.region_id
        )

This filters `Project.region_id` on a `Budget` query without a JOIN.
SQLAlchemy emits an implicit cross-join → Cartesian product. Net
effect: REGION_MANAGER and AREA_MANAGER users were seeing zero
overrun alerts (or wrong counts) regardless of actual data.

Fix: use the denormalized `Budget.region_id` / `Budget.area_id`
columns directly. Both exist on the Budget model (verified at
budget.py:74-79). The /financial-summary endpoint already uses
this pattern — we now match it.

Tests
-----
We don't run real SQL here. Instead, we use a query-spy stub that
records every `.filter(...)` clause. The test asserts:
1. After the fix, the `Budget.region_id` clause is present (not
   `Project.region_id`).
2. The Budget filter chain is monotonic — no Cartesian explosion
   from a stray Project clause.
"""
import asyncio
from unittest.mock import MagicMock

import pytest

from app.routers.dashboard import get_dashboard_alerts
from app.models import Budget, Project


def _user(role_code, *, perms=None, user_id=1, region_id=None, area_id=None):
    user = MagicMock()
    user.id = user_id
    user.role_id = 1
    user.is_active = True
    user.region_id = region_id
    user.area_id = area_id
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = [MagicMock(code=p) for p in (perms or set())]
    user._permissions = set(perms or set())
    return user


class _SpyDBStub:
    """Minimal SQLAlchemy session that captures the filter chain
    used on each query. Lets us assert WHICH model's column was
    used in the WHERE — the heart of the bug."""

    def __init__(self, *, overrun_count=0):
        self._current_model = None
        self._overrun_count = overrun_count
        self.filter_columns: list = []  # column names referenced

    def query(self, *args):
        first = args[0] if args else None
        self._current_model = getattr(first, "__name__", str(first))
        return self

    def filter(self, *clauses, **kwargs):
        for c in clauses:
            # SQLAlchemy clause objects expose .left / .right; for a
            # simple `Column == value`, .left.table.name and
            # .left.name give us the table+column reference.
            try:
                left = getattr(c, "left", None)
                if left is not None:
                    table = getattr(getattr(left, "table", None), "name", None)
                    column = getattr(left, "name", None)
                    if table and column:
                        self.filter_columns.append(f"{table}.{column}")
            except Exception:
                pass
        return self

    def count(self):
        # Only Budget queries land here in /alerts
        if self._current_model == "Budget":
            return self._overrun_count
        return 0


# ===========================================================================
# Bug-fix coverage — region/area filter routes through Budget, not Project
# ===========================================================================

class TestAlertsScopeFix:

    def test_region_manager_filters_on_budget_region_not_project(self):
        """The fix: filter chain uses Budget.region_id, not
        Project.region_id."""
        db = _SpyDBStub(overrun_count=3)
        asyncio.run(get_dashboard_alerts(
            db=db,
            current_user=_user("REGION_MANAGER",
                               perms={"dashboard.view"}, region_id=5),
            limit=5,
        ))
        # The bug used 'projects.region_id'. The fix uses 'budgets.region_id'.
        assert any("budgets.region_id" in c for c in db.filter_columns), (
            f"Expected a Budget.region_id filter; got {db.filter_columns}. "
            "If this fails, the SQL bug from Wave 2.2.c regressed."
        )
        assert not any("projects.region_id" in c for c in db.filter_columns), (
            f"Found a Project.region_id filter on a Budget query — that's "
            f"the original bug. Filters: {db.filter_columns}"
        )

    def test_area_manager_filters_on_budget_area_not_project(self):
        db = _SpyDBStub(overrun_count=2)
        asyncio.run(get_dashboard_alerts(
            db=db,
            current_user=_user("AREA_MANAGER",
                               perms={"dashboard.view"}, area_id=12),
            limit=5,
        ))
        assert any("budgets.area_id" in c for c in db.filter_columns), (
            f"Expected a Budget.area_id filter; got {db.filter_columns}."
        )
        assert not any("projects.area_id" in c for c in db.filter_columns), (
            f"Found a Project.area_id filter on a Budget query — that's "
            f"the original bug. Filters: {db.filter_columns}"
        )


class TestAlertsCount:
    """End-to-end happy paths — verify the alert count surfaces in
    the response when the filter chain is correct."""

    def test_admin_sees_all_overruns(self):
        db = _SpyDBStub(overrun_count=7)
        result = asyncio.run(get_dashboard_alerts(
            db=db, current_user=_user("ADMIN"), limit=5,
        ))
        # Admin path doesn't add region/area filters
        assert not any("budgets.region_id" in c or "budgets.area_id" in c
                       for c in db.filter_columns)
        # The overrun alert is present
        budget_alerts = [a for a in result if a.get("title") == "חריגות תקציב"]
        assert budget_alerts and budget_alerts[0]["count"] == 7

    def test_region_manager_overrun_count_returned(self):
        db = _SpyDBStub(overrun_count=4)
        result = asyncio.run(get_dashboard_alerts(
            db=db,
            current_user=_user("REGION_MANAGER",
                               perms={"dashboard.view"}, region_id=5),
            limit=5,
        ))
        budget_alerts = [a for a in result if a.get("title") == "חריגות תקציב"]
        assert budget_alerts and budget_alerts[0]["count"] == 4

    def test_area_manager_overrun_count_returned(self):
        db = _SpyDBStub(overrun_count=2)
        result = asyncio.run(get_dashboard_alerts(
            db=db,
            current_user=_user("AREA_MANAGER",
                               perms={"dashboard.view"}, area_id=12),
            limit=5,
        ))
        budget_alerts = [a for a in result if a.get("title") == "חריגות תקציב"]
        assert budget_alerts and budget_alerts[0]["count"] == 2

    def test_no_alerts_when_count_is_zero(self):
        db = _SpyDBStub(overrun_count=0)
        result = asyncio.run(get_dashboard_alerts(
            db=db,
            current_user=_user("REGION_MANAGER",
                               perms={"dashboard.view"}, region_id=5),
            limit=5,
        ))
        budget_alerts = [a for a in result if a.get("title") == "חריגות תקציב"]
        assert not budget_alerts, "Zero overruns should not produce an alert"
