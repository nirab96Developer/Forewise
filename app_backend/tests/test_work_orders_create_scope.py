"""
Phase 3 Wave 1.3.e — POST /work-orders pre-create scope check.

Closes the leak documented in PHASE3_WAVE13_RECON.md (row 3): any
role with `work_orders.create` could create a WO inside any project,
regardless of region/area/assignment. Now the project_id from the
payload is fetched and scope-checked via ProjectScopeStrategy before
the service runs.

Behavior preserved for rootless WOs (data.project_id is None) — RBAC
alone, exactly as today.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.work_orders import create_work_order
from app.routers import work_orders as wo_router


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


def _project(*, project_id=10, region_id=None, area_id=None):
    p = MagicMock()
    p.id = project_id
    p.region_id = region_id
    p.area_id = area_id
    return p


def _payload(project_id=10):
    """WorkOrderCreate payload — only the field create() inspects on
    the auth path."""
    p = MagicMock()
    p.project_id = project_id
    return p


class _DBStub:
    def __init__(self, *, project=None, assignment=None):
        self._project = project
        self._assignment = assignment
        self._current_model = None

    def query(self, *args):
        first = args[0] if args else None
        self._current_model = getattr(first, "__name__", str(first))
        return self

    def filter(self, *a, **kw):
        return self

    def first(self):
        if self._current_model == "Project":
            return self._project
        if self._current_model == "ProjectAssignment":
            return self._assignment
        return None


@pytest.fixture(autouse=True)
def _mock_service(monkeypatch):
    fake = MagicMock()
    fake.create.return_value = MagicMock(id=1, project_id=10, status="PENDING")
    monkeypatch.setattr(wo_router, "work_order_service", fake)
    monkeypatch.setattr(wo_router, "notify_work_order_created", lambda *a, **k: None)
    return fake


# ===========================================================================
# Global roles — pass for any project
# ===========================================================================

class TestCreateAdmin:

    def test_admin_can_create_in_any_project(self, _mock_service):
        db = _DBStub(project=_project(region_id=99, area_id=99))
        create_work_order(_payload(), db, _user("ADMIN"))
        _mock_service.create.assert_called_once()

    def test_coordinator_can_create_in_any_project(self, _mock_service):
        db = _DBStub(project=_project(region_id=99, area_id=99))
        create_work_order(
            _payload(),
            db,
            _user("ORDER_COORDINATOR", perms={"work_orders.create"}),
        )
        _mock_service.create.assert_called_once()


# ===========================================================================
# REGION_MANAGER
# ===========================================================================

class TestCreateRegionManager:

    def test_in_region_passes(self, _mock_service):
        db = _DBStub(project=_project(region_id=5))
        create_work_order(
            _payload(),
            db,
            _user("REGION_MANAGER", perms={"work_orders.create"}, region_id=5),
        )
        _mock_service.create.assert_called_once()

    def test_out_of_region_403(self, _mock_service):
        db = _DBStub(project=_project(region_id=99))
        with pytest.raises(HTTPException) as exc:
            create_work_order(
                _payload(),
                db,
                _user("REGION_MANAGER", perms={"work_orders.create"}, region_id=5),
            )
        assert exc.value.status_code == 403
        _mock_service.create.assert_not_called()


# ===========================================================================
# AREA_MANAGER
# ===========================================================================

class TestCreateAreaManager:

    def test_in_area_passes(self, _mock_service):
        db = _DBStub(project=_project(area_id=12))
        create_work_order(
            _payload(),
            db,
            _user("AREA_MANAGER", perms={"work_orders.create"}, area_id=12),
        )
        _mock_service.create.assert_called_once()

    def test_out_of_area_403(self, _mock_service):
        db = _DBStub(project=_project(area_id=99))
        with pytest.raises(HTTPException) as exc:
            create_work_order(
                _payload(),
                db,
                _user("AREA_MANAGER", perms={"work_orders.create"}, area_id=12),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# WORK_MANAGER
# ===========================================================================

class TestCreateWorkManager:

    def test_assigned_project_passes(self, _mock_service):
        assignment = MagicMock(user_id=7, project_id=10, is_active=True)
        db = _DBStub(project=_project(project_id=10), assignment=assignment)
        create_work_order(
            _payload(project_id=10),
            db,
            _user("WORK_MANAGER", perms={"work_orders.create"}, user_id=7),
        )
        _mock_service.create.assert_called_once()

    def test_unassigned_project_403(self, _mock_service):
        db = _DBStub(project=_project(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            create_work_order(
                _payload(project_id=99),
                db,
                _user("WORK_MANAGER", perms={"work_orders.create"}, user_id=7),
            )
        assert exc.value.status_code == 403
        _mock_service.create.assert_not_called()


# ===========================================================================
# Blocked roles
# ===========================================================================

class TestCreateBlockedRoles:

    def test_supplier_blocked_by_perm_403(self, _mock_service):
        """SUPPLIER lacks work_orders.create in DB; require_permission
        fires before we even reach the project lookup."""
        db = _DBStub(project=_project())
        with pytest.raises(HTTPException) as exc:
            create_work_order(
                _payload(),
                db,
                _user("SUPPLIER", perms={"work_orders.read_own"}),
            )
        assert exc.value.status_code == 403

    def test_supplier_with_create_perm_blocked_by_strategy_403(self, _mock_service):
        """Belt-and-braces: even if work_orders.create were ever
        granted to SUPPLIER by mistake, ProjectScopeStrategy still
        denies them."""
        db = _DBStub(project=_project())
        with pytest.raises(HTTPException) as exc:
            create_work_order(
                _payload(),
                db,
                _user("SUPPLIER", perms={"work_orders.create"}),
            )
        assert exc.value.status_code == 403

    def test_accountant_blocked_by_perm_403(self, _mock_service):
        db = _DBStub(project=_project())
        with pytest.raises(HTTPException) as exc:
            create_work_order(
                _payload(),
                db,
                _user("ACCOUNTANT", perms={"work_orders.read"}),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# project_id edge cases
# ===========================================================================

class TestProjectIdEdgeCases:

    def test_missing_project_404(self, _mock_service):
        """Payload references a project that doesn't exist → 404
        BEFORE the service is invoked."""
        db = _DBStub(project=None)
        with pytest.raises(HTTPException) as exc:
            create_work_order(_payload(project_id=999), db, _user("ADMIN"))
        assert exc.value.status_code == 404
        _mock_service.create.assert_not_called()

    def test_rootless_wo_admin_passes(self, _mock_service):
        """project_id is None → strategy not invoked (legacy flow).
        Admin succeeds via RBAC alone, exactly as today."""
        db = _DBStub(project=None)
        create_work_order(_payload(project_id=None), db, _user("ADMIN"))
        _mock_service.create.assert_called_once()

    def test_rootless_wo_non_global_uses_legacy_behavior(self, _mock_service):
        """Pin the legacy escape hatch: when project_id is None we do
        NOT scope-check (no project to compare). RBAC is the only
        gate. This preserves any field-team flow that creates WOs
        without a project up front."""
        db = _DBStub(project=None)
        create_work_order(
            _payload(project_id=None),
            db,
            _user("REGION_MANAGER", perms={"work_orders.create"}, region_id=5),
        )
        _mock_service.create.assert_called_once()
