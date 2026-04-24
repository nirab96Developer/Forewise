"""
Tests for permission + scope enforcement on /api/v1/budgets/{id}/{detail,committed,spent}.

Phase 2 Wave 5 — these three endpoints used to leak financial data
(supplier names, hourly rates, worklog amounts) to ANY authenticated
user, including SUPPLIER. Wave 5 added:
  - require_permission(current_user, "budgets.read") — gate the SUPPLIER
    role out (and any other role missing budgets.read).
  - _check_budget_scope(db, user, budget) — region/area/project scope
    per role, so even a budgets.read holder can only see their own
    region/area/assigned-project budgets.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.budgets import (
    _check_budget_scope,
    get_budget_detail,
    get_budget_committed,
    get_budget_spent,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _user(
    role_code: str,
    *,
    user_id: int = 1,
    region_id: int | None = None,
    area_id: int | None = None,
    perms: set[str] | None = None,
):
    user = MagicMock()
    user.id = user_id
    user.is_active = True
    user.role_id = 1
    user.region_id = region_id
    user.area_id = area_id
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = [MagicMock(code=p) for p in (perms or set())]
    user._permissions = set(perms or set())
    return user


def _budget(
    *,
    budget_id: int = 1,
    region_id: int | None = None,
    area_id: int | None = None,
    project_id: int | None = None,
):
    b = MagicMock()
    b.id = budget_id
    b.region_id = region_id
    b.area_id = area_id
    b.project_id = project_id
    b.is_active = True
    b.total_amount = 1000
    b.committed_amount = 200
    b.spent_amount = 100
    b.status = "ACTIVE"
    b.fiscal_year = 2026
    b.name = "Test Budget"
    return b


class _DBStub:
    """Minimal SQLAlchemy session stub.

    Hands back the seeded budget for `db.query(Budget).filter(...).first()`,
    the seeded project assignment for `db.query(ProjectAssignment)...`, and
    empty results for any other model. Also handles the raw `db.execute(...)`
    that get_budget_detail uses to pull budget_items.
    """

    def __init__(self, budget=None, assignment=None):
        self._budget = budget
        self._assignment = assignment
        self._current_model = None

    def query(self, model):
        self._current_model = getattr(model, "__name__", str(model))
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        if self._current_model == "Budget":
            return self._budget
        if self._current_model == "ProjectAssignment":
            return self._assignment
        return None

    def all(self):
        return []

    def execute(self, *args, **kwargs):
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        return cursor


# ---------------------------------------------------------------------------
# Helper unit tests — _check_budget_scope
# ---------------------------------------------------------------------------

class TestCheckBudgetScopeAdmin:
    def test_admin_passes(self):
        _check_budget_scope(_DBStub(), _user("ADMIN"), _budget())

    def test_super_admin_passes(self):
        _check_budget_scope(_DBStub(), _user("SUPER_ADMIN"), _budget())


class TestCheckBudgetScopeRegionManager:
    def test_in_scope_passes(self):
        u = _user("REGION_MANAGER", region_id=5)
        _check_budget_scope(_DBStub(), u, _budget(region_id=5))

    def test_out_of_scope_403(self):
        u = _user("REGION_MANAGER", region_id=5)
        with pytest.raises(HTTPException) as exc:
            _check_budget_scope(_DBStub(), u, _budget(region_id=99))
        assert exc.value.status_code == 403

    def test_no_region_id_403(self):
        u = _user("REGION_MANAGER", region_id=None)
        with pytest.raises(HTTPException) as exc:
            _check_budget_scope(_DBStub(), u, _budget(region_id=5))
        assert exc.value.status_code == 403


class TestCheckBudgetScopeAreaManager:
    def test_in_scope_passes(self):
        u = _user("AREA_MANAGER", area_id=10)
        _check_budget_scope(_DBStub(), u, _budget(area_id=10))

    def test_out_of_scope_403(self):
        u = _user("AREA_MANAGER", area_id=10)
        with pytest.raises(HTTPException) as exc:
            _check_budget_scope(_DBStub(), u, _budget(area_id=11))
        assert exc.value.status_code == 403


class TestCheckBudgetScopeAccountant:
    def test_area_match_passes(self):
        u = _user("ACCOUNTANT", area_id=10, region_id=99)
        _check_budget_scope(_DBStub(), u, _budget(area_id=10, region_id=5))

    def test_region_match_passes(self):
        u = _user("ACCOUNTANT", area_id=99, region_id=5)
        _check_budget_scope(_DBStub(), u, _budget(area_id=20, region_id=5))

    def test_neither_matches_403(self):
        u = _user("ACCOUNTANT", area_id=10, region_id=5)
        with pytest.raises(HTTPException) as exc:
            _check_budget_scope(_DBStub(), u, _budget(area_id=99, region_id=99))
        assert exc.value.status_code == 403


class TestCheckBudgetScopeWorkManager:
    def test_assigned_project_passes(self):
        u = _user("WORK_MANAGER", user_id=42)
        assignment = MagicMock()
        assignment.user_id = 42
        assignment.project_id = 7
        assignment.is_active = True
        db = _DBStub(assignment=assignment)
        _check_budget_scope(db, u, _budget(project_id=7))

    def test_unassigned_project_403(self):
        u = _user("WORK_MANAGER", user_id=42)
        db = _DBStub(assignment=None)
        with pytest.raises(HTTPException) as exc:
            _check_budget_scope(db, u, _budget(project_id=7))
        assert exc.value.status_code == 403

    def test_budget_with_no_project_403(self):
        u = _user("WORK_MANAGER", user_id=42)
        db = _DBStub()
        with pytest.raises(HTTPException) as exc:
            _check_budget_scope(db, u, _budget(project_id=None))
        assert exc.value.status_code == 403


class TestCheckBudgetScopeUnknownRoles:
    def test_supplier_403(self):
        u = _user("SUPPLIER")
        with pytest.raises(HTTPException) as exc:
            _check_budget_scope(_DBStub(), u, _budget())
        assert exc.value.status_code == 403

    def test_field_worker_403(self):
        u = _user("FIELD_WORKER")
        with pytest.raises(HTTPException) as exc:
            _check_budget_scope(_DBStub(), u, _budget())
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Endpoint integration tests — require_permission + scope wired correctly
# ---------------------------------------------------------------------------

class TestEndpointsRequirePermission:
    """SUPPLIER hits require_permission first and gets 403 before scope ever runs."""

    def test_detail_supplier_blocked(self):
        u = _user("SUPPLIER")
        db = _DBStub(budget=_budget(region_id=5))
        with pytest.raises(HTTPException) as exc:
            get_budget_detail(budget_id=1, db=db, current_user=u)
        assert exc.value.status_code == 403

    def test_committed_supplier_blocked(self):
        u = _user("SUPPLIER")
        db = _DBStub(budget=_budget(project_id=7))
        with pytest.raises(HTTPException) as exc:
            get_budget_committed(budget_id=1, db=db, current_user=u)
        assert exc.value.status_code == 403

    def test_spent_supplier_blocked(self):
        u = _user("SUPPLIER")
        db = _DBStub(budget=_budget(project_id=7))
        with pytest.raises(HTTPException) as exc:
            get_budget_spent(budget_id=1, db=db, current_user=u)
        assert exc.value.status_code == 403


class TestEndpointsAdminBypass:
    """ADMIN passes both require_permission (built-in bypass) and scope check."""

    def test_detail_admin_passes_cross_region(self):
        u = _user("ADMIN")
        db = _DBStub(budget=_budget(region_id=999, area_id=999, project_id=999))
        result = get_budget_detail(budget_id=1, db=db, current_user=u)
        assert result["id"] == 1

    def test_committed_admin_passes(self):
        u = _user("ADMIN")
        db = _DBStub(budget=_budget(region_id=999, project_id=7))
        result = get_budget_committed(budget_id=1, db=db, current_user=u)
        assert result["total"] == 0  # no WOs from stub

    def test_spent_admin_passes(self):
        u = _user("ADMIN")
        db = _DBStub(budget=_budget(region_id=999, project_id=7))
        result = get_budget_spent(budget_id=1, db=db, current_user=u)
        assert result["total"] == 0  # no worklogs from stub


class TestEndpointsScopeBlocks:
    """User has budgets.read but tries to read a budget outside their scope."""

    def test_detail_region_manager_cross_region_blocked(self):
        # Has budgets.read (passes permission gate) but wrong region → scope blocks
        u = _user("REGION_MANAGER", region_id=5, perms={"budgets.read"})
        db = _DBStub(budget=_budget(region_id=99))
        with pytest.raises(HTTPException) as exc:
            get_budget_detail(budget_id=1, db=db, current_user=u)
        assert exc.value.status_code == 403

    def test_committed_area_manager_cross_area_blocked(self):
        u = _user("AREA_MANAGER", area_id=10, perms={"budgets.read"})
        db = _DBStub(budget=_budget(area_id=99, project_id=7))
        with pytest.raises(HTTPException) as exc:
            get_budget_committed(budget_id=1, db=db, current_user=u)
        assert exc.value.status_code == 403

    def test_spent_work_manager_unassigned_project_blocked(self):
        u = _user("WORK_MANAGER", user_id=42, perms={"budgets.read"})
        db = _DBStub(
            budget=_budget(project_id=7),
            assignment=None,
        )
        with pytest.raises(HTTPException) as exc:
            get_budget_spent(budget_id=1, db=db, current_user=u)
        assert exc.value.status_code == 403


class TestEndpointsScopeAllows:
    """User in scope passes both gates."""

    def test_detail_region_manager_in_scope_passes(self):
        u = _user("REGION_MANAGER", region_id=5, perms={"budgets.read"})
        db = _DBStub(budget=_budget(region_id=5))
        result = get_budget_detail(budget_id=1, db=db, current_user=u)
        assert result["id"] == 1

    def test_committed_area_manager_in_scope_passes(self):
        u = _user("AREA_MANAGER", area_id=10, perms={"budgets.read"})
        db = _DBStub(budget=_budget(area_id=10, project_id=7))
        result = get_budget_committed(budget_id=1, db=db, current_user=u)
        assert result["total"] == 0

    def test_spent_work_manager_assigned_passes(self):
        u = _user("WORK_MANAGER", user_id=42, perms={"budgets.read"})
        assignment = MagicMock()
        assignment.user_id = 42
        assignment.project_id = 7
        assignment.is_active = True
        db = _DBStub(budget=_budget(project_id=7), assignment=assignment)
        result = get_budget_spent(budget_id=1, db=db, current_user=u)
        assert result["total"] == 0
