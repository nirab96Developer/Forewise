"""
Phase 3 Wave 1.3.e — direct unit tests for ProjectScopeStrategy.

The strategy is invoked from POST /work-orders for pre-create scope
checks. Future create-style endpoints (Budgets, SupplierRotations,
etc.) can reuse it without changes.

Tests pin the role × outcome matrix so a future regression in
GLOBAL_ROLES, in WORK_MANAGER's assignment query, or in field-name
attributes (region_id / area_id) gets caught immediately.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.authorization import AuthorizationService
from app.core.authorization.scope_strategies import ProjectScopeStrategy


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


class _DBStub:
    def __init__(self, *, assignment=None):
        self._assignment = assignment
        self._current_model = None

    def query(self, *args):
        first = args[0] if args else None
        self._current_model = getattr(first, "__name__", str(first))
        return self

    def filter(self, *a, **kw):
        return self

    def first(self):
        if self._current_model == "ProjectAssignment":
            return self._assignment
        return None


# ===========================================================================
# Global roles
# ===========================================================================

class TestGlobalRoles:

    def test_admin_passes(self):
        ProjectScopeStrategy().check(_DBStub(), _user("ADMIN"), _project(region_id=99, area_id=99))

    def test_super_admin_passes(self):
        ProjectScopeStrategy().check(_DBStub(), _user("SUPER_ADMIN"), _project(region_id=99, area_id=99))

    def test_coordinator_passes(self):
        ProjectScopeStrategy().check(_DBStub(), _user("ORDER_COORDINATOR"), _project(region_id=99, area_id=99))

    def test_accountant_passes_strategy(self):
        """ACCOUNTANT is global at the strategy level. The endpoint
        gates them on RBAC (work_orders.create not granted), so they
        never actually call the strategy in production."""
        ProjectScopeStrategy().check(_DBStub(), _user("ACCOUNTANT"), _project(region_id=99))


# ===========================================================================
# REGION_MANAGER
# ===========================================================================

class TestRegionManager:

    def test_in_region_passes(self):
        ProjectScopeStrategy().check(
            _DBStub(),
            _user("REGION_MANAGER", region_id=5),
            _project(region_id=5),
        )

    def test_cross_region_403(self):
        with pytest.raises(HTTPException) as exc:
            ProjectScopeStrategy().check(
                _DBStub(),
                _user("REGION_MANAGER", region_id=5),
                _project(region_id=99),
            )
        assert exc.value.status_code == 403

    def test_user_without_region_403(self):
        with pytest.raises(HTTPException) as exc:
            ProjectScopeStrategy().check(
                _DBStub(),
                _user("REGION_MANAGER", region_id=None),
                _project(region_id=5),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# AREA_MANAGER
# ===========================================================================

class TestAreaManager:

    def test_in_area_passes(self):
        ProjectScopeStrategy().check(
            _DBStub(),
            _user("AREA_MANAGER", area_id=12),
            _project(area_id=12),
        )

    def test_cross_area_403(self):
        with pytest.raises(HTTPException) as exc:
            ProjectScopeStrategy().check(
                _DBStub(),
                _user("AREA_MANAGER", area_id=12),
                _project(area_id=99),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# WORK_MANAGER
# ===========================================================================

class TestWorkManager:

    def test_assigned_project_passes(self):
        assignment = MagicMock(user_id=7, project_id=10, is_active=True)
        ProjectScopeStrategy().check(
            _DBStub(assignment=assignment),
            _user("WORK_MANAGER", user_id=7),
            _project(project_id=10),
        )

    def test_unassigned_project_403(self):
        with pytest.raises(HTTPException) as exc:
            ProjectScopeStrategy().check(
                _DBStub(assignment=None),
                _user("WORK_MANAGER", user_id=7),
                _project(project_id=99),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# SUPPLIER + unknown roles
# ===========================================================================

class TestBlockedRoles:

    def test_supplier_403(self):
        with pytest.raises(HTTPException) as exc:
            ProjectScopeStrategy().check(_DBStub(), _user("SUPPLIER"), _project())
        assert exc.value.status_code == 403

    def test_field_worker_403(self):
        with pytest.raises(HTTPException) as exc:
            ProjectScopeStrategy().check(_DBStub(), _user("FIELD_WORKER"), _project())
        assert exc.value.status_code == 403

    def test_unknown_role_403(self):
        with pytest.raises(HTTPException) as exc:
            ProjectScopeStrategy().check(_DBStub(), _user("MYSTERY_ROLE"), _project())
        assert exc.value.status_code == 403


# ===========================================================================
# AuthorizationService wiring — make sure resource_type="Project"
# routes to ProjectScopeStrategy and not the WorkOrder one.
# ===========================================================================

class TestServiceWiring:

    def test_authorize_project_routes_to_project_strategy(self):
        svc = AuthorizationService(_DBStub())
        with pytest.raises(HTTPException) as exc:
            svc.authorize(
                _user("REGION_MANAGER", region_id=5),
                resource=_project(region_id=99),
                resource_type="Project",
            )
        assert exc.value.status_code == 403

    def test_authorize_admin_passes_via_service(self):
        svc = AuthorizationService(_DBStub())
        svc.authorize(
            _user("ADMIN"),
            resource=_project(region_id=99),
            resource_type="Project",
        )
