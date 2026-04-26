"""
Tests for the WorkOrder scope strategy (Phase 3 Wave 1.2).

Closes the list-vs-detail leak documented in
PHASE3_WAVE12_FRONTEND_RECON.md. Every (role × WorkOrder) combination
verified at the strategy layer; a couple of integration cases exercise
the service end-to-end.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.authorization import AuthorizationService
from app.core.authorization.scope_strategies import WorkOrderScopeStrategy


def _user(role_code: str, *, perms=None, user_id=1, region_id=None, area_id=None):
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


def _wo(*, wo_id=1, project_id=10, status="PENDING"):
    wo = MagicMock()
    wo.id = wo_id
    wo.project_id = project_id
    wo.status = status
    return wo


def _project(*, project_id=10, region_id=None, area_id=None):
    p = MagicMock()
    p.id = project_id
    p.region_id = region_id
    p.area_id = area_id
    return p


class _DBStub:
    """Stub that returns a seeded project for the strategy's
    `_project_for(...)` lookup, and a seeded ProjectAssignment for
    WORK_MANAGER's `assigned` query."""

    def __init__(self, project=None, assignment=None):
        self._project = project
        self._assignment = assignment
        self._current = None

    def query(self, model):
        self._current = getattr(model, "__name__", str(model))
        return self

    def filter(self, *a, **kw):
        return self

    def first(self):
        if self._current == "Project":
            return self._project
        if self._current == "ProjectAssignment":
            return self._assignment
        return None

    def all(self):
        return []

    def subquery(self):
        return self


# ===========================================================================
# Global roles — see everything
# ===========================================================================

class TestGlobalRoles:

    def test_admin_passes_anything(self):
        s = WorkOrderScopeStrategy()
        s.check(_DBStub(), _user("ADMIN"), _wo())

    def test_coordinator_passes_anything(self):
        s = WorkOrderScopeStrategy()
        s.check(_DBStub(), _user("ORDER_COORDINATOR"), _wo())

    def test_accountant_passes_anything(self):
        s = WorkOrderScopeStrategy()
        s.check(_DBStub(), _user("ACCOUNTANT"), _wo())


# ===========================================================================
# REGION_MANAGER — region match via WO.project.region_id
# ===========================================================================

class TestRegionManager:

    def test_in_region_passes(self):
        s = WorkOrderScopeStrategy()
        s.check(
            _DBStub(project=_project(region_id=5)),
            _user("REGION_MANAGER", region_id=5),
            _wo(project_id=10),
        )

    def test_cross_region_403(self):
        s = WorkOrderScopeStrategy()
        with pytest.raises(HTTPException) as exc:
            s.check(
                _DBStub(project=_project(region_id=99)),
                _user("REGION_MANAGER", region_id=5),
                _wo(),
            )
        assert exc.value.status_code == 403

    def test_no_user_region_id_403(self):
        s = WorkOrderScopeStrategy()
        with pytest.raises(HTTPException) as exc:
            s.check(
                _DBStub(project=_project(region_id=5)),
                _user("REGION_MANAGER", region_id=None),
                _wo(),
            )
        assert exc.value.status_code == 403

    def test_wo_with_no_project_403(self):
        """A WO that somehow has project_id=None must not leak to a
        non-global role."""
        s = WorkOrderScopeStrategy()
        with pytest.raises(HTTPException) as exc:
            s.check(
                _DBStub(project=None),
                _user("REGION_MANAGER", region_id=5),
                _wo(project_id=None),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# AREA_MANAGER — area match via WO.project.area_id
# ===========================================================================

class TestAreaManager:

    def test_in_area_passes(self):
        s = WorkOrderScopeStrategy()
        s.check(
            _DBStub(project=_project(area_id=10)),
            _user("AREA_MANAGER", area_id=10),
            _wo(),
        )

    def test_cross_area_403(self):
        s = WorkOrderScopeStrategy()
        with pytest.raises(HTTPException) as exc:
            s.check(
                _DBStub(project=_project(area_id=99)),
                _user("AREA_MANAGER", area_id=10),
                _wo(),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# WORK_MANAGER — only assigned projects (closes the URL-leak)
# ===========================================================================

class TestWorkManager:

    def test_assigned_project_passes(self):
        s = WorkOrderScopeStrategy()
        assignment = MagicMock(user_id=42, project_id=10, is_active=True)
        s.check(
            _DBStub(assignment=assignment),
            _user("WORK_MANAGER", user_id=42),
            _wo(project_id=10),
        )

    def test_unassigned_project_403_via_direct_url(self):
        """The list-vs-detail leak: in legacy code a work_manager could
        load `/work-orders/X` even when X wasn't in their list. The
        strategy now closes the gap."""
        s = WorkOrderScopeStrategy()
        with pytest.raises(HTTPException) as exc:
            s.check(
                _DBStub(assignment=None),
                _user("WORK_MANAGER", user_id=42),
                _wo(project_id=99),
            )
        assert exc.value.status_code == 403

    def test_wo_with_no_project_403(self):
        s = WorkOrderScopeStrategy()
        with pytest.raises(HTTPException) as exc:
            s.check(
                _DBStub(assignment=None),
                _user("WORK_MANAGER", user_id=42),
                _wo(project_id=None),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# SUPPLIER + unknown roles — denied
# ===========================================================================

class TestSupplierAndUnknown:

    def test_supplier_403(self):
        s = WorkOrderScopeStrategy()
        with pytest.raises(HTTPException) as exc:
            s.check(_DBStub(), _user("SUPPLIER"), _wo())
        assert exc.value.status_code == 403

    def test_field_worker_403(self):
        s = WorkOrderScopeStrategy()
        with pytest.raises(HTTPException) as exc:
            s.check(_DBStub(), _user("FIELD_WORKER"), _wo())
        assert exc.value.status_code == 403


# ===========================================================================
# AuthorizationService integration — verifies the strategy is wired
# ===========================================================================

class TestAuthorizationServiceWiring:
    """End-to-end through the service surface so a future refactor of
    the registry doesn't silently bypass the strategy."""

    def test_authorize_runs_workorder_strategy_via_resource_type(self):
        svc = AuthorizationService(_DBStub(project=_project(region_id=99)))
        with pytest.raises(HTTPException) as exc:
            svc.authorize(
                _user("REGION_MANAGER", region_id=5, perms={"work_orders.read"}),
                "work_orders.read",
                resource=_wo(),
                resource_type="WorkOrder",
            )
        assert exc.value.status_code == 403

    def test_authorize_admin_passes_via_service(self):
        svc = AuthorizationService(_DBStub())
        svc.authorize(
            _user("ADMIN"),
            "work_orders.read",
            resource=_wo(),
            resource_type="WorkOrder",
        )

    def test_authorize_supplier_blocked_via_service(self):
        svc = AuthorizationService(_DBStub())
        with pytest.raises(HTTPException) as exc:
            svc.authorize(
                _user("SUPPLIER", perms={"work_orders.read"}),
                "work_orders.read",
                resource=_wo(),
                resource_type="WorkOrder",
            )
        assert exc.value.status_code == 403
