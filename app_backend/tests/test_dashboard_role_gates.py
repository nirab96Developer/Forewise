"""
Phase 3 Wave 2.2.e — role gates for role-specific dashboard
endpoints.

Closes the "no role gate" gaps from PHASE3_WAVE22_RECON.md
section 1: 5-6 endpoints that were intended for one specific
role each but had no backend enforcement. The UI routes per
role today, so end-user impact was zero — but the backend
defense-in-depth was missing.

Endpoints + allowed roles
-------------------------
  /work-manager-summary    → WORK_MANAGER + ADMIN/SUPER_ADMIN
  /work-manager-overview   → WORK_MANAGER + ADMIN/SUPER_ADMIN  (alias)
  /region-overview         → REGION_MANAGER + ADMIN/SUPER_ADMIN
  /area-overview           → AREA_MANAGER + REGION_MANAGER +
                             ADMIN/SUPER_ADMIN
  /coordinator-queue       → ORDER_COORDINATOR + ADMIN/SUPER_ADMIN
  /region-areas            → REGION_MANAGER + ADMIN/SUPER_ADMIN

Strategy: a single _require_role helper raises 403 for any role
not in the allowed list. Tests pin both the allow side (intended
roles pass) and the deny side (every other production role 403s).
"""
import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.dashboard import (
    _require_role,
    get_work_manager_summary,
    get_work_manager_overview,
    get_region_overview,
    get_area_overview,
    get_coordinator_queue,
    get_region_areas_breakdown,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(role_code, *, perms=None, user_id=1, region_id=None, area_id=None):
    user = MagicMock()
    user.id = user_id
    user.role_id = 1
    user.is_active = True
    user.region_id = region_id
    user.area_id = area_id
    user.full_name = f"User {user_id}"
    user.username = f"user_{user_id}"
    user.region = MagicMock(name="region", id=region_id) if region_id else None
    user.area = MagicMock(name="area", id=area_id) if area_id else None
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = [MagicMock(code=p) for p in (perms or set())]
    user._permissions = set(perms or set())
    return user


class _NoOpDB:
    """DB stub that returns 0/empty for everything. The body of the
    endpoint may run after the role gate passes; we don't care
    about the response shape — only that 403 vs success matches the
    expected role policy.

    `.first()` returns a benign MagicMock (instead of None) so any
    `db.query(User).filter(...).first()` re-fetch in the body works
    without AttributeError. region_id/area_id default to None so
    the body's "if not user.region_id: return []" exits cleanly."""

    def execute(self, *a, **kw):
        cursor = MagicMock()
        cursor.scalar.return_value = 0
        cursor.fetchall.return_value = []
        cursor.first.return_value = None
        return cursor

    def query(self, *a, **kw):
        return self

    def filter(self, *a, **kw):
        return self

    def options(self, *a, **kw):
        return self

    def all(self):
        return []

    def first(self):
        # Body code may re-fetch the user — return a benign object
        # whose region_id/area_id are None so the body short-circuits.
        stub = MagicMock()
        stub.region_id = None
        stub.area_id = None
        return stub


# ===========================================================================
# Helper unit test
# ===========================================================================

class TestRequireRoleHelper:

    def test_allowed_role_passes(self):
        _require_role(_user("WORK_MANAGER"), "WORK_MANAGER")

    def test_role_not_in_list_403(self):
        with pytest.raises(HTTPException) as exc:
            _require_role(_user("ACCOUNTANT"), "WORK_MANAGER")
        assert exc.value.status_code == 403

    def test_case_insensitive_match(self):
        """Accept lowercase entries in the allowed list."""
        _require_role(_user("ADMIN"), "admin")

    def test_no_role_user_403(self):
        u = MagicMock()
        u.role = None
        with pytest.raises(HTTPException) as exc:
            _require_role(u, "ADMIN")
        assert exc.value.status_code == 403

    def test_first_match_wins(self):
        _require_role(_user("ADMIN"), "WORK_MANAGER", "ADMIN", "SUPER_ADMIN")


# ===========================================================================
# /work-manager-summary + /work-manager-overview
# ===========================================================================

class TestWorkManagerEndpoints:
    """WORK_MANAGER + ADMIN/SUPER_ADMIN allowed; everyone else 403."""

    def _call_summary(self, user):
        return asyncio.run(get_work_manager_summary(
            db=_NoOpDB(), current_user=user,
        ))

    def _call_overview(self, user):
        return asyncio.run(get_work_manager_overview(
            db=_NoOpDB(), current_user=user,
        ))

    def test_work_manager_passes_summary(self):
        result = self._call_summary(_user("WORK_MANAGER", user_id=7))
        assert "hours_this_week" in result

    def test_admin_passes_summary(self):
        result = self._call_summary(_user("ADMIN"))
        assert "hours_this_week" in result

    def test_super_admin_passes_summary(self):
        self._call_summary(_user("SUPER_ADMIN"))

    def test_work_manager_passes_overview_alias(self):
        result = self._call_overview(_user("WORK_MANAGER", user_id=7))
        assert "hours_this_week" in result

    def test_admin_passes_overview_alias(self):
        self._call_overview(_user("ADMIN"))

    @pytest.mark.parametrize("role", [
        "REGION_MANAGER", "AREA_MANAGER", "ORDER_COORDINATOR",
        "ACCOUNTANT", "FIELD_WORKER", "SUPPLIER",
    ])
    def test_other_roles_403_summary(self, role):
        with pytest.raises(HTTPException) as exc:
            self._call_summary(_user(role))
        assert exc.value.status_code == 403

    @pytest.mark.parametrize("role", [
        "REGION_MANAGER", "AREA_MANAGER", "ORDER_COORDINATOR",
        "ACCOUNTANT", "FIELD_WORKER", "SUPPLIER",
    ])
    def test_other_roles_403_overview(self, role):
        with pytest.raises(HTTPException) as exc:
            self._call_overview(_user(role))
        assert exc.value.status_code == 403


# ===========================================================================
# /region-overview
# ===========================================================================

class TestRegionOverviewGate:
    """REGION_MANAGER + ADMIN/SUPER_ADMIN allowed; everyone else 403."""

    def _call(self, user):
        return asyncio.run(get_region_overview(
            db=_NoOpDB(), current_user=user,
        ))

    def test_region_manager_passes(self):
        self._call(_user("REGION_MANAGER", region_id=5))

    def test_admin_passes(self):
        self._call(_user("ADMIN", region_id=5))

    def test_super_admin_passes(self):
        self._call(_user("SUPER_ADMIN", region_id=5))

    @pytest.mark.parametrize("role", [
        "AREA_MANAGER", "WORK_MANAGER", "ORDER_COORDINATOR",
        "ACCOUNTANT", "FIELD_WORKER", "SUPPLIER",
    ])
    def test_other_roles_403(self, role):
        with pytest.raises(HTTPException) as exc:
            self._call(_user(role))
        assert exc.value.status_code == 403


# ===========================================================================
# /area-overview
# ===========================================================================

class TestAreaOverviewGate:
    """AREA_MANAGER + REGION_MANAGER + ADMIN/SUPER_ADMIN allowed."""

    def _call(self, user):
        return asyncio.run(get_area_overview(
            db=_NoOpDB(), current_user=user,
        ))

    def test_area_manager_passes(self):
        self._call(_user("AREA_MANAGER", area_id=12))

    def test_region_manager_passes(self):
        """REGION_MANAGER can drill into one of their areas."""
        self._call(_user("REGION_MANAGER", region_id=5, area_id=12))

    def test_admin_passes(self):
        self._call(_user("ADMIN", area_id=12))

    @pytest.mark.parametrize("role", [
        "WORK_MANAGER", "ORDER_COORDINATOR",
        "ACCOUNTANT", "FIELD_WORKER", "SUPPLIER",
    ])
    def test_other_roles_403(self, role):
        with pytest.raises(HTTPException) as exc:
            self._call(_user(role))
        assert exc.value.status_code == 403


# ===========================================================================
# /coordinator-queue
# ===========================================================================

class TestCoordinatorQueueGate:
    """ORDER_COORDINATOR + ADMIN/SUPER_ADMIN allowed."""

    def _call(self, user):
        return asyncio.run(get_coordinator_queue(
            status_filter="", project_id="", search="",
            db=_NoOpDB(), current_user=user,
        ))

    def test_coordinator_passes(self):
        self._call(_user("ORDER_COORDINATOR"))

    def test_admin_passes(self):
        self._call(_user("ADMIN"))

    @pytest.mark.parametrize("role", [
        "REGION_MANAGER", "AREA_MANAGER", "WORK_MANAGER",
        "ACCOUNTANT", "FIELD_WORKER", "SUPPLIER",
    ])
    def test_other_roles_403(self, role):
        with pytest.raises(HTTPException) as exc:
            self._call(_user(role))
        assert exc.value.status_code == 403


# ===========================================================================
# /region-areas
# ===========================================================================

class TestRegionAreasGate:
    """REGION_MANAGER + ADMIN/SUPER_ADMIN allowed."""

    def _call(self, user):
        return asyncio.run(get_region_areas_breakdown(
            db=_NoOpDB(), current_user=user,
        ))

    def test_region_manager_passes(self):
        self._call(_user("REGION_MANAGER", region_id=5))

    def test_admin_passes(self):
        self._call(_user("ADMIN"))

    def test_super_admin_passes(self):
        self._call(_user("SUPER_ADMIN"))

    @pytest.mark.parametrize("role", [
        "AREA_MANAGER", "WORK_MANAGER", "ORDER_COORDINATOR",
        "ACCOUNTANT", "FIELD_WORKER", "SUPPLIER",
    ])
    def test_other_roles_403(self, role):
        with pytest.raises(HTTPException) as exc:
            self._call(_user(role))
        assert exc.value.status_code == 403
