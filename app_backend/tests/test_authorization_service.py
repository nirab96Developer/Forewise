"""
Tests for the new centralized AuthorizationService (Phase 3 Wave 1).

Wave 1 ships only the Budget strategy. These tests verify:
  1. The service runs the three layers in the right order
     (RBAC → ABAC → state).
  2. Budget strategy outputs match the legacy _check_budget_scope
     for every (role, region/area/project) combination — behavior
     identity is the success criterion for this wave.
  3. Domains without a registered strategy fall through cleanly
     (no false 403, no crash).
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.authorization import AuthorizationService
from app.core.authorization.scope_strategies import BudgetScopeStrategy


def _user(role_code: str, *, perms: set[str] | None = None,
          user_id: int = 1, region_id=None, area_id=None):
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


def _budget(*, region_id=None, area_id=None, project_id=None):
    b = MagicMock()
    b.id = 1
    b.region_id = region_id
    b.area_id = area_id
    b.project_id = project_id
    b.status = "ACTIVE"
    return b


class _DBStub:
    def __init__(self, assignment=None):
        self._assignment = assignment

    def query(self, *a, **kw):
        return self

    def filter(self, *a, **kw):
        return self

    def first(self):
        return self._assignment

    def subquery(self):
        return self


# ===========================================================================
# Layer order
# ===========================================================================

class TestLayerOrder:

    def test_rbac_runs_first(self):
        """No `budgets.read` permission → 403 raised before scope check
        gets the chance to run."""
        svc = AuthorizationService(_DBStub())
        u = _user("SUPPLIER", perms=set())
        with pytest.raises(HTTPException) as exc:
            svc.authorize(u, "budgets.read", resource=_budget(region_id=5),
                          resource_type="Budget")
        assert exc.value.status_code == 403

    def test_abac_runs_when_action_omitted(self):
        """Without an action, the service skips RBAC and goes straight
        to scope. AREA_MANAGER cross-area → 403 from the strategy."""
        svc = AuthorizationService(_DBStub())
        u = _user("AREA_MANAGER", area_id=10)
        with pytest.raises(HTTPException) as exc:
            svc.authorize(u, action=None,
                          resource=_budget(area_id=99),
                          resource_type="Budget")
        assert exc.value.status_code == 403

    def test_state_guard_blocks_when_status_not_allowed(self):
        svc = AuthorizationService(_DBStub())
        u = _user("ADMIN")
        b = _budget(region_id=5)
        b.status = "CLOSED"
        with pytest.raises(HTTPException) as exc:
            svc.authorize(
                u, action=None, resource=b, resource_type="Budget",
                context={"allowed_statuses": ["ACTIVE", "DRAFT"]},
            )
        assert exc.value.status_code == 409

    def test_state_guard_passes_when_status_allowed(self):
        svc = AuthorizationService(_DBStub())
        svc.authorize(
            _user("ADMIN"), action=None, resource=_budget(region_id=5),
            resource_type="Budget",
            context={"allowed_statuses": ["ACTIVE", "DRAFT"]},
        )

    def test_unregistered_resource_skips_scope(self):
        """Strategies dict has only Budget. Other types pass through
        (matches the gradual-migration plan)."""
        svc = AuthorizationService(_DBStub())
        # Some random non-budget resource
        random_resource = MagicMock()
        random_resource.status = "X"
        svc.authorize(
            _user("ADMIN"), action=None,
            resource=random_resource, resource_type="UnknownType",
        )


# ===========================================================================
# Behavior identity vs legacy _check_budget_scope
# ===========================================================================

class TestBehaviorIdentityWithLegacyCheck:
    """For every role × budget combo Wave 5 covered, the new service
    must produce the same raise/pass decision as the original helper."""

    def setup_method(self):
        self.strategy = BudgetScopeStrategy()
        self.svc = AuthorizationService(_DBStub())

    def test_admin_always_passes(self):
        self.svc.authorize(_user("ADMIN"), action=None,
                           resource=_budget(region_id=99), resource_type="Budget")

    def test_region_manager_in_scope(self):
        u = _user("REGION_MANAGER", region_id=5)
        self.svc.authorize(u, action=None,
                           resource=_budget(region_id=5), resource_type="Budget")

    def test_region_manager_out_of_scope(self):
        u = _user("REGION_MANAGER", region_id=5)
        with pytest.raises(HTTPException) as exc:
            self.svc.authorize(u, action=None,
                               resource=_budget(region_id=99), resource_type="Budget")
        assert exc.value.status_code == 403

    def test_area_manager_in_scope(self):
        u = _user("AREA_MANAGER", area_id=10)
        self.svc.authorize(u, action=None,
                           resource=_budget(area_id=10), resource_type="Budget")

    def test_area_manager_out_of_scope(self):
        u = _user("AREA_MANAGER", area_id=10)
        with pytest.raises(HTTPException) as exc:
            self.svc.authorize(u, action=None,
                               resource=_budget(area_id=99), resource_type="Budget")
        assert exc.value.status_code == 403

    def test_accountant_area_match(self):
        u = _user("ACCOUNTANT", area_id=10, region_id=99)
        self.svc.authorize(u, action=None,
                           resource=_budget(area_id=10, region_id=5), resource_type="Budget")

    def test_accountant_region_match(self):
        u = _user("ACCOUNTANT", area_id=99, region_id=5)
        self.svc.authorize(u, action=None,
                           resource=_budget(area_id=20, region_id=5), resource_type="Budget")

    def test_accountant_neither_match(self):
        u = _user("ACCOUNTANT", area_id=10, region_id=5)
        with pytest.raises(HTTPException) as exc:
            self.svc.authorize(u, action=None,
                               resource=_budget(area_id=99, region_id=99), resource_type="Budget")
        assert exc.value.status_code == 403

    def test_work_manager_assigned_project(self):
        assignment = MagicMock(user_id=42, project_id=7, is_active=True)
        svc = AuthorizationService(_DBStub(assignment=assignment))
        u = _user("WORK_MANAGER", user_id=42)
        svc.authorize(u, action=None,
                      resource=_budget(project_id=7), resource_type="Budget")

    def test_work_manager_unassigned_project(self):
        svc = AuthorizationService(_DBStub(assignment=None))
        u = _user("WORK_MANAGER", user_id=42)
        with pytest.raises(HTTPException) as exc:
            svc.authorize(u, action=None,
                          resource=_budget(project_id=7), resource_type="Budget")
        assert exc.value.status_code == 403

    def test_supplier_blocked(self):
        u = _user("SUPPLIER", perms={"equipment.read"})
        with pytest.raises(HTTPException) as exc:
            self.svc.authorize(u, action=None,
                               resource=_budget(), resource_type="Budget")
        assert exc.value.status_code == 403


# ===========================================================================
# filter_query — narrows a list query per role
# ===========================================================================

class TestFilterQuery:
    """Unit-test the strategy.filter outputs by spying on what gets
    .filter()'d on the query."""

    def setup_method(self):
        self.svc = AuthorizationService(_DBStub())

    def test_admin_query_unchanged(self):
        sentinel = object()
        # Strategy.filter returns query unchanged for global roles.
        result = self.svc.filter_query(_user("ADMIN"), sentinel, "Budget")
        assert result is sentinel

    def test_unknown_resource_type_passes_through(self):
        sentinel = object()
        result = self.svc.filter_query(_user("ADMIN"), sentinel, "Unknown")
        assert result is sentinel

    def test_region_manager_filter_invoked(self):
        """Verifying the chain runs without error using a stub query."""
        class StubQuery:
            def __init__(self):
                self.filter_called_with = []
            def filter(self, *args, **kwargs):
                self.filter_called_with.append((args, kwargs))
                return self

        q = StubQuery()
        u = _user("REGION_MANAGER", region_id=5)
        result = self.svc.filter_query(u, q, "Budget")
        assert result is q
        assert len(q.filter_called_with) == 1
