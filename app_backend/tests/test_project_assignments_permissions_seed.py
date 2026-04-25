"""
Tests for Wave 7.E.1 — project_assignments permission seed migration.

This is a data-migration wave (no router changes), so the tests verify:
  1. The 6 new permission codes are in the DB.
  2. Each new permission is wired to the correct roles per the matrix
     in WAVE7E_PLAN.md.
  3. require_permission() resolves correctly for every (role, perm)
     combination — admin bypass, in-matrix users pass, out-of-matrix
     users get 403.
  4. The two non-permission endpoints stay non-permission:
     - GET /my-assignments → self-service via current_user.id
     - GET /roles/list     → static enum, auth-only
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.dependencies import require_permission


NEW_PERMS = [
    "project_assignments.update",
    "project_assignments.complete",
    "project_assignments.transfer",
    "project_assignments.bulk_assign",
    "project_assignments.check_availability",
    "project_assignments.check_conflicts",
]

EXPECTED_ASSIGNMENTS = {
    "project_assignments.update":             {"ADMIN", "REGION_MANAGER"},
    "project_assignments.complete":           {"ADMIN", "REGION_MANAGER", "AREA_MANAGER", "WORK_MANAGER"},
    "project_assignments.transfer":           {"ADMIN", "REGION_MANAGER"},
    "project_assignments.bulk_assign":        {"ADMIN", "REGION_MANAGER"},
    "project_assignments.check_availability": {"ADMIN", "REGION_MANAGER", "AREA_MANAGER"},
    "project_assignments.check_conflicts":    {"ADMIN", "REGION_MANAGER", "AREA_MANAGER"},
}


# ---------------------------------------------------------------------------
# DB-level verification
# ---------------------------------------------------------------------------

class TestDBPermissionsSeeded:
    """Verifies the migration actually inserted what it claims."""

    def test_all_six_perms_exist(self):
        db = SessionLocal()
        try:
            placeholders = ", ".join(f":p{i}" for i in range(len(NEW_PERMS)))
            params = {f"p{i}": code for i, code in enumerate(NEW_PERMS)}
            rows = db.execute(
                text(f"SELECT code FROM permissions WHERE code IN ({placeholders})"),
                params,
            ).fetchall()
            present = {r[0] for r in rows}
            missing = set(NEW_PERMS) - present
            assert not missing, f"Missing perms in DB: {missing}"
        finally:
            db.close()

    @pytest.mark.parametrize("perm_code", NEW_PERMS)
    def test_perm_assigned_to_expected_roles(self, perm_code):
        db = SessionLocal()
        try:
            rows = db.execute(
                text(
                    """
                    SELECT r.code FROM role_permissions rp
                    JOIN roles r ON r.id = rp.role_id
                    JOIN permissions p ON p.id = rp.permission_id
                    WHERE p.code = :code
                    """
                ),
                {"code": perm_code},
            ).fetchall()
            actual = {r[0] for r in rows}
            expected = EXPECTED_ASSIGNMENTS[perm_code]
            assert actual == expected, (
                f"{perm_code}: expected {expected}, got {actual}"
            )
        finally:
            db.close()


# ---------------------------------------------------------------------------
# require_permission resolution per role
# ---------------------------------------------------------------------------

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


class TestRequirePermissionResolution:
    """End-to-end: with the new perms in DB, does require_permission()
    accept/reject the expected callers? Mocked-user variant — exercises
    the in-process function, not HTTP."""

    def test_admin_bypass_complete(self):
        # Admin doesn't even need the perm in user._permissions
        require_permission(_user("ADMIN"), "project_assignments.complete")

    def test_work_manager_can_complete(self):
        u = _user("WORK_MANAGER", perms={"project_assignments.complete"})
        require_permission(u, "project_assignments.complete")

    def test_work_manager_cannot_update(self):
        u = _user("WORK_MANAGER", perms={"project_assignments.complete"})
        with pytest.raises(HTTPException) as exc:
            require_permission(u, "project_assignments.update")
        assert exc.value.status_code == 403

    def test_area_manager_can_check_availability(self):
        u = _user("AREA_MANAGER", perms={"project_assignments.check_availability"})
        require_permission(u, "project_assignments.check_availability")

    def test_area_manager_cannot_transfer(self):
        u = _user("AREA_MANAGER", perms={"project_assignments.check_availability"})
        with pytest.raises(HTTPException) as exc:
            require_permission(u, "project_assignments.transfer")
        assert exc.value.status_code == 403

    def test_region_manager_can_bulk_assign(self):
        u = _user("REGION_MANAGER", perms={"project_assignments.bulk_assign"})
        require_permission(u, "project_assignments.bulk_assign")

    def test_supplier_blocked_on_every_new_perm(self):
        u = _user("SUPPLIER", perms={"equipment.read"})
        for perm in NEW_PERMS:
            with pytest.raises(HTTPException) as exc:
                require_permission(u, perm)
            assert exc.value.status_code == 403, (
                f"SUPPLIER unexpectedly passed {perm}"
            )

    def test_accountant_blocked_on_every_new_perm(self):
        u = _user("ACCOUNTANT", perms={"invoices.read"})
        for perm in NEW_PERMS:
            with pytest.raises(HTTPException) as exc:
                require_permission(u, perm)
            assert exc.value.status_code == 403, (
                f"ACCOUNTANT unexpectedly passed {perm}"
            )


# ---------------------------------------------------------------------------
# Non-permission endpoints — confirm they stayed self-service / public
# ---------------------------------------------------------------------------

class TestNonPermissionEndpoints:
    """Lock in the design choice: /my-assignments and /roles/list don't
    require any project_assignments.* permission."""

    def test_my_assignments_handler_has_no_require_permission_dep(self):
        from app.routers.project_assignments import get_my_assignments
        # FastAPI stores deps on the function via a closure / signature.
        # Easiest robust check: read the source.
        import inspect
        src = inspect.getsource(get_my_assignments)
        assert "require_permission" not in src, (
            "get_my_assignments must stay self-service (current_user.id)"
        )

    def test_roles_list_handler_has_no_require_permission_dep(self):
        from app.routers.project_assignments import get_assignment_roles
        import inspect
        src = inspect.getsource(get_assignment_roles)
        assert "require_permission" not in src, (
            "get_assignment_roles is a static enum; auth-only is intentional"
        )


# ---------------------------------------------------------------------------
# No remaining unseeded project_assignments.* perms
# ---------------------------------------------------------------------------

class TestNoMissingPermissionsAfterWave7E1:
    """After this wave, every project_assignments.* perm referenced by
    the router must exist in DB. If a future commit adds a new
    require_permission("project_assignments.X") without seeding X, this
    test should fail."""

    def test_every_router_perm_is_seeded(self):
        import re, inspect
        from app.routers import project_assignments as pa_router

        src = inspect.getsource(pa_router)
        used = set(re.findall(
            r"require_permission\(['\"](project_assignments\.[a-z_]+)['\"]",
            src,
        ))

        db = SessionLocal()
        try:
            rows = db.execute(text(
                "SELECT code FROM permissions WHERE code LIKE 'project_assignments%'"
            )).fetchall()
            seeded = {r[0] for r in rows}
        finally:
            db.close()

        missing = used - seeded
        assert not missing, (
            f"Router uses perms missing from DB: {missing}. "
            f"Add them in a follow-up seed migration."
        )
