"""
Phase 3 Wave 3.1.6.a — direct unit tests for WorklogScopeStrategy.

Pin the role × outcome matrix at the strategy layer. Each role gets
explicit pass/403 cases for all three scope dimensions:
  - global (admin/coordinator/accountant)
  - own only (supplier, field worker)
  - project (region/area/work_mgr)

These tests cover the strategy contract; router-level integration
tests (test_worklogs_read_scope.py) cover the endpoints themselves.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.authorization import AuthorizationService
from app.core.authorization.scope_strategies import WorklogScopeStrategy


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


def _worklog(*, wl_id=1, project_id=10, user_id=1, work_order_id=None):
    w = MagicMock()
    w.id = wl_id
    w.project_id = project_id
    w.user_id = user_id
    w.work_order_id = work_order_id
    w.status = "DRAFT"
    return w


def _project(*, project_id=10, region_id=None, area_id=None):
    p = MagicMock()
    p.id = project_id
    p.region_id = region_id
    p.area_id = area_id
    return p


class _DBStub:
    def __init__(self, *, project=None, work_order=None, assignment=None):
        self._project = project
        self._work_order = work_order
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
        if self._current_model == "WorkOrder":
            return self._work_order
        if self._current_model == "ProjectAssignment":
            return self._assignment
        return None

    def all(self):
        return []

    def subquery(self):
        return self


# ===========================================================================
# Global roles
# ===========================================================================

class TestGlobalRoles:

    def test_admin_passes_anything(self):
        WorklogScopeStrategy().check(_DBStub(), _user("ADMIN"), _worklog())

    def test_super_admin_passes_anything(self):
        WorklogScopeStrategy().check(_DBStub(), _user("SUPER_ADMIN"), _worklog())

    def test_coordinator_passes_anything(self):
        WorklogScopeStrategy().check(_DBStub(), _user("ORDER_COORDINATOR"), _worklog())

    def test_accountant_passes_anything(self):
        WorklogScopeStrategy().check(_DBStub(), _user("ACCOUNTANT"), _worklog())


# ===========================================================================
# OWN_ONLY roles — by user_id
# ===========================================================================

class TestSupplier:

    def test_own_worklog_passes(self):
        WorklogScopeStrategy().check(
            _DBStub(),
            _user("SUPPLIER", user_id=42),
            _worklog(user_id=42),
        )

    def test_other_user_worklog_403(self):
        with pytest.raises(HTTPException) as exc:
            WorklogScopeStrategy().check(
                _DBStub(),
                _user("SUPPLIER", user_id=42),
                _worklog(user_id=999),
            )
        assert exc.value.status_code == 403


class TestFieldWorker:

    def test_own_worklog_passes(self):
        WorklogScopeStrategy().check(
            _DBStub(),
            _user("FIELD_WORKER", user_id=42),
            _worklog(user_id=42),
        )

    def test_other_user_worklog_403(self):
        with pytest.raises(HTTPException) as exc:
            WorklogScopeStrategy().check(
                _DBStub(),
                _user("FIELD_WORKER", user_id=42),
                _worklog(user_id=999),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# REGION_MANAGER — by project.region_id
# ===========================================================================

class TestRegionManager:

    def test_in_region_passes(self):
        WorklogScopeStrategy().check(
            _DBStub(project=_project(region_id=5)),
            _user("REGION_MANAGER", region_id=5),
            _worklog(),
        )

    def test_cross_region_403(self):
        with pytest.raises(HTTPException) as exc:
            WorklogScopeStrategy().check(
                _DBStub(project=_project(region_id=99)),
                _user("REGION_MANAGER", region_id=5),
                _worklog(),
            )
        assert exc.value.status_code == 403

    def test_no_user_region_id_403(self):
        with pytest.raises(HTTPException) as exc:
            WorklogScopeStrategy().check(
                _DBStub(project=_project(region_id=5)),
                _user("REGION_MANAGER", region_id=None),
                _worklog(),
            )
        assert exc.value.status_code == 403

    def test_worklog_with_no_project_403(self):
        """Defensive: a worklog with no project_id and no work_order_id
        is unscope-able and must not leak."""
        with pytest.raises(HTTPException) as exc:
            WorklogScopeStrategy().check(
                _DBStub(project=None),
                _user("REGION_MANAGER", region_id=5),
                _worklog(project_id=None, work_order_id=None),
            )
        assert exc.value.status_code == 403

    def test_falls_back_through_work_order(self):
        """If worklog.project_id is None but work_order_id is set,
        resolve project via the WO."""
        wo = MagicMock(project_id=10)
        WorklogScopeStrategy().check(
            _DBStub(project=_project(region_id=5), work_order=wo),
            _user("REGION_MANAGER", region_id=5),
            _worklog(project_id=None, work_order_id=99),
        )


# ===========================================================================
# AREA_MANAGER — by project.area_id
# ===========================================================================

class TestAreaManager:

    def test_in_area_passes(self):
        WorklogScopeStrategy().check(
            _DBStub(project=_project(area_id=12)),
            _user("AREA_MANAGER", area_id=12),
            _worklog(),
        )

    def test_cross_area_403(self):
        with pytest.raises(HTTPException) as exc:
            WorklogScopeStrategy().check(
                _DBStub(project=_project(area_id=99)),
                _user("AREA_MANAGER", area_id=12),
                _worklog(),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# WORK_MANAGER — by project_assignment
# ===========================================================================

class TestWorkManager:

    def test_assigned_project_passes(self):
        assignment = MagicMock(user_id=7, project_id=10, is_active=True)
        WorklogScopeStrategy().check(
            _DBStub(assignment=assignment),
            _user("WORK_MANAGER", user_id=7),
            _worklog(project_id=10),
        )

    def test_unassigned_project_403(self):
        with pytest.raises(HTTPException) as exc:
            WorklogScopeStrategy().check(
                _DBStub(assignment=None),
                _user("WORK_MANAGER", user_id=7),
                _worklog(project_id=99),
            )
        assert exc.value.status_code == 403

    def test_no_project_id_falls_through_via_work_order(self):
        """Worklog with no direct project_id but linked WO with project_id."""
        wo = MagicMock(project_id=10)
        assignment = MagicMock(user_id=7, project_id=10, is_active=True)
        WorklogScopeStrategy().check(
            _DBStub(project=_project(project_id=10), work_order=wo, assignment=assignment),
            _user("WORK_MANAGER", user_id=7),
            _worklog(project_id=None, work_order_id=99),
        )


# ===========================================================================
# Unknown role → blocked
# ===========================================================================

class TestUnknownRole:

    def test_unknown_role_403(self):
        with pytest.raises(HTTPException) as exc:
            WorklogScopeStrategy().check(
                _DBStub(),
                _user("MYSTERY", user_id=1),
                _worklog(user_id=99),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# AuthorizationService wiring
# ===========================================================================

class TestServiceWiring:

    def test_authorize_routes_to_worklog_strategy(self):
        svc = AuthorizationService(_DBStub(project=_project(region_id=99)))
        with pytest.raises(HTTPException) as exc:
            svc.authorize(
                _user("REGION_MANAGER", region_id=5),
                resource=_worklog(),
                resource_type="Worklog",
            )
        assert exc.value.status_code == 403

    def test_authorize_admin_passes_via_service(self):
        svc = AuthorizationService(_DBStub())
        svc.authorize(
            _user("ADMIN"),
            resource=_worklog(),
            resource_type="Worklog",
        )

    def test_authorize_supplier_other_user_403(self):
        svc = AuthorizationService(_DBStub())
        with pytest.raises(HTTPException) as exc:
            svc.authorize(
                _user("SUPPLIER", user_id=42),
                resource=_worklog(user_id=999),
                resource_type="Worklog",
            )
        assert exc.value.status_code == 403
