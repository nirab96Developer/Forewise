"""
Tests for Wave Dashboard — `dashboard.view` permission lock.

Strategic decision after Wave 7.J: scope-filter alone is not enough
for the dashboard. The dashboard returns merged financial / KPI /
activity data; "scope filter to empty" is not the same as "permission
denied". This wave adds an explicit gate via the existing
DASHBOARD.VIEW permission row, plus revokes it from SUPPLIER (the
only role that should never see the internal manager dashboard).

Migration `a3b4c5d6e7f8` revoked SUPPLIER → DASHBOARD.VIEW.
Router gained a single shared `_dashboard_view` dependency that calls
`require_permission(current_user, "dashboard.view")` BEFORE any
handler runs. Every dashboard endpoint now uses
`Depends(_dashboard_view)` instead of `Depends(get_current_user)`.

Tests verify:
  * SUPPLIER → 403 from the helper itself.
  * Any role with dashboard.view passes the helper.
  * The migration's role-permission state is what we expect.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from app.core.database import SessionLocal
from app.routers.dashboard import _dashboard_view


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


# ---------------------------------------------------------------------------
# DB-level: migration applied correctly
# ---------------------------------------------------------------------------

class TestDashboardViewAssignment:
    """Migration a3b4c5d6e7f8 must leave DASHBOARD.VIEW assigned to all
    six manager-class roles, NOT to SUPPLIER."""

    def test_supplier_does_not_have_dashboard_view(self):
        db = SessionLocal()
        try:
            row = db.execute(text(
                """
                SELECT 1 FROM role_permissions rp
                JOIN roles r ON r.id = rp.role_id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE r.code = 'SUPPLIER' AND p.code = 'DASHBOARD.VIEW'
                """
            )).fetchone()
            assert row is None, (
                "SUPPLIER must NOT have DASHBOARD.VIEW after migration "
                "a3b4c5d6e7f8. Run alembic upgrade head."
            )
        finally:
            db.close()

    def test_six_roles_keep_dashboard_view(self):
        db = SessionLocal()
        try:
            rows = db.execute(text(
                """
                SELECT r.code FROM role_permissions rp
                JOIN roles r ON r.id = rp.role_id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE p.code = 'DASHBOARD.VIEW'
                ORDER BY r.code
                """
            )).fetchall()
            actual = {r[0] for r in rows}
            expected = {
                "ACCOUNTANT", "ADMIN", "AREA_MANAGER",
                "ORDER_COORDINATOR", "REGION_MANAGER", "WORK_MANAGER",
            }
            assert actual == expected, (
                f"DASHBOARD.VIEW assignment drift. Expected {expected}, got {actual}."
            )
        finally:
            db.close()


# ---------------------------------------------------------------------------
# _dashboard_view dependency — the gate every handler now sits behind
# ---------------------------------------------------------------------------

class TestDashboardViewDependency:

    def test_admin_passes(self):
        u = _user("ADMIN")
        assert _dashboard_view(current_user=u) is u

    def test_region_manager_with_perm_passes(self):
        u = _user("REGION_MANAGER", perms={"dashboard.view"})
        assert _dashboard_view(current_user=u) is u

    def test_area_manager_with_perm_passes(self):
        u = _user("AREA_MANAGER", perms={"dashboard.view"})
        assert _dashboard_view(current_user=u) is u

    def test_work_manager_with_perm_passes(self):
        u = _user("WORK_MANAGER", perms={"dashboard.view"})
        assert _dashboard_view(current_user=u) is u

    def test_accountant_with_perm_passes(self):
        u = _user("ACCOUNTANT", perms={"dashboard.view"})
        assert _dashboard_view(current_user=u) is u

    def test_coordinator_with_perm_passes(self):
        u = _user("ORDER_COORDINATOR", perms={"dashboard.view"})
        assert _dashboard_view(current_user=u) is u

    def test_supplier_blocked_403(self):
        """Supplier with NO dashboard.view (matches DB after migration)
        must be blocked from every /dashboard/* endpoint at the gate."""
        u = _user("SUPPLIER", perms={"equipment.read"})
        with pytest.raises(HTTPException) as exc:
            _dashboard_view(current_user=u)
        assert exc.value.status_code == 403

    def test_user_with_no_perms_blocked_403(self):
        """A non-admin role that doesn't have dashboard.view loaded
        (e.g. mid-migration state) must be blocked."""
        u = _user("WORK_MANAGER", perms={"work_orders.read"})
        with pytest.raises(HTTPException) as exc:
            _dashboard_view(current_user=u)
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Wiring check — every /dashboard/* handler now uses _dashboard_view
# ---------------------------------------------------------------------------

class TestEveryHandlerUsesDashboardView:
    """Lock-in: a future commit can't quietly add a new dashboard
    endpoint that bypasses the gate by using Depends(get_current_user)
    instead of Depends(_dashboard_view)."""

    def test_no_handler_uses_get_current_user_directly(self):
        import inspect
        from app.routers import dashboard as dashboard_mod

        src = inspect.getsource(dashboard_mod)
        # The helper itself is allowed to call get_current_user.
        # No other handler should.
        # Count Depends(get_current_user) calls and assert <=1.
        import re
        matches = re.findall(r"Depends\(get_current_user\)", src)
        assert len(matches) == 1, (
            f"Expected exactly 1 Depends(get_current_user) (inside the "
            f"_dashboard_view helper). Found {len(matches)}. A handler "
            f"is bypassing the dashboard.view gate."
        )

    def test_dashboard_view_helper_is_widely_used(self):
        import inspect
        from app.routers import dashboard as dashboard_mod

        src = inspect.getsource(dashboard_mod)
        import re
        matches = re.findall(r"Depends\(_dashboard_view\)", src)
        # 23 endpoints, each takes the gate; expect >= 20 to be safe
        # against minor variations.
        assert len(matches) >= 20, (
            f"Expected ~23 handlers to use Depends(_dashboard_view). "
            f"Found only {len(matches)}."
        )
