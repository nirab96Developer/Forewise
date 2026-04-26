"""
Phase 3 Wave 2.2.b — role gate on /dashboard/accountant-overview.

Closes leak D2 from PHASE3_WAVE22_RECON.md: before this commit,
any caller with `dashboard.view` could pull system-wide financial
KPIs and the worklogs-pending-review list, including costs and
hourly rates. The only intended audience is finance.

Decision (per user direction):
  ALLOW: ACCOUNTANT, ADMIN, SUPER_ADMIN
  DENY:  REGION_MANAGER, AREA_MANAGER, WORK_MANAGER, FIELD_WORKER,
         ORDER_COORDINATOR (has their own /coordinator-queue),
         SUPPLIER (already 403 at dashboard.view in production)

ACCOUNTANT keeps cross-region financial visibility — no scope
narrowing here. That's intentional: ACCOUNTANT is a global
finance role.
"""
import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.dashboard import get_accountant_overview


def _user(role_code, *, perms=None, user_id=1, region_id=None, area_id=None):
    user = MagicMock()
    user.id = user_id
    user.role_id = 1
    user.is_active = True
    user.region_id = region_id
    user.area_id = area_id
    user.full_name = f"User {user_id}"
    user.username = f"user_{user_id}"
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = [MagicMock(code=p) for p in (perms or set())]
    user._permissions = set(perms or set())
    return user


class _DBStub:
    """Minimal session — every db.execute(...).scalar() returns 0
    or a stub cursor. The endpoint runs through happy-path with no
    real data; we're only testing the role gate."""

    def execute(self, *a, **kw):
        cursor = MagicMock()
        cursor.scalar.return_value = 0
        cursor.fetchall.return_value = []
        cursor.first.return_value = None
        return cursor


# ===========================================================================
# Allowed roles
# ===========================================================================

class TestAccountantOverviewAllowed:
    """ACCOUNTANT, ADMIN, SUPER_ADMIN must be able to open the
    dashboard. The legitimate UX path."""

    def _call(self, user):
        return asyncio.run(get_accountant_overview(
            status_filter="SUBMITTED", project_id="", supplier_id="", search="",
            db=_DBStub(), current_user=user,
        ))

    def test_accountant_passes(self):
        result = self._call(_user("ACCOUNTANT", perms={"dashboard.view"}))
        assert "kpis" in result
        assert "worklogs" in result

    def test_admin_passes(self):
        result = self._call(_user("ADMIN"))
        assert "kpis" in result

    def test_super_admin_passes(self):
        result = self._call(_user("SUPER_ADMIN", perms={"dashboard.view"}))
        assert "kpis" in result


# ===========================================================================
# Denied roles
# ===========================================================================

class TestAccountantOverviewDenied:
    """The leak-closure: every other role gets 403. Pin each one
    explicitly so a future role-table change can't accidentally
    re-open the gap."""

    def _call(self, user):
        return asyncio.run(get_accountant_overview(
            status_filter="SUBMITTED", project_id="", supplier_id="", search="",
            db=_DBStub(), current_user=user,
        ))

    def test_region_manager_403(self):
        with pytest.raises(HTTPException) as exc:
            self._call(_user("REGION_MANAGER",
                             perms={"dashboard.view"}, region_id=5))
        assert exc.value.status_code == 403

    def test_area_manager_403(self):
        with pytest.raises(HTTPException) as exc:
            self._call(_user("AREA_MANAGER",
                             perms={"dashboard.view"}, area_id=12))
        assert exc.value.status_code == 403

    def test_work_manager_403(self):
        with pytest.raises(HTTPException) as exc:
            self._call(_user("WORK_MANAGER", perms={"dashboard.view"}))
        assert exc.value.status_code == 403

    def test_field_worker_403(self):
        with pytest.raises(HTTPException) as exc:
            self._call(_user("FIELD_WORKER", perms={"dashboard.view"}))
        assert exc.value.status_code == 403

    def test_order_coordinator_403(self):
        """COORDINATOR is intentionally NOT included — they have
        their own /coordinator-queue. If product later wants them
        to see financials, that's a deliberate addition."""
        with pytest.raises(HTTPException) as exc:
            self._call(_user("ORDER_COORDINATOR", perms={"dashboard.view"}))
        assert exc.value.status_code == 403

    def test_supplier_403(self):
        """SUPPLIER doesn't hold dashboard.view in production, so
        this 403 comes from the new role gate (or the
        require_permission gate above it). Both layers test the
        same thing in this case — they should both block."""
        with pytest.raises(HTTPException) as exc:
            self._call(_user("SUPPLIER", perms={"dashboard.view"}))
        assert exc.value.status_code == 403

    def test_unknown_role_403(self):
        """Defensive: an unrecognized role code can't sneak through."""
        with pytest.raises(HTTPException) as exc:
            self._call(_user("MYSTERY_ROLE", perms={"dashboard.view"}))
        assert exc.value.status_code == 403
