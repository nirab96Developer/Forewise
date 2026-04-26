"""
Phase 3 Wave 1.3.a — scope enforcement on work_orders write endpoints.

Closes the leak documented in PHASE3_WAVE13_RECON.md, where an
AREA_MANAGER could PATCH a WO outside their area, or a WORK_MANAGER
could /start a WO on a project they're not assigned to, just by
calling the URL directly.

Each endpoint tested for:
  - admin / coordinator pass (global roles)
  - in-scope role passes (region/area/work-mgr on assigned)
  - out-of-scope role gets 403 (the regression test)
  - missing WO → 404
  - SUPPLIER → 403 (defense-in-depth — already blocked by perm anyway)

Tests run with mocked DB + mocked WorkOrderService so we exercise
ONLY the auth pipeline. Behavior of the service itself is verified
in test_work_orders_crud.py.
"""
from unittest.mock import MagicMock, patch
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.routers import work_orders as wo_router
from app.routers.work_orders import (
    update_work_order,
    delete_work_order,
    cancel_work_order,
    close_work_order,
    start_work_order,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

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


def _wo(*, wo_id=42, project_id=10, status="PENDING"):
    wo = MagicMock()
    wo.id = wo_id
    wo.project_id = project_id
    wo.status = status
    wo.deleted_at = None
    wo.order_number = f"WO-{wo_id}"
    return wo


def _project(*, project_id=10, region_id=None, area_id=None):
    p = MagicMock()
    p.id = project_id
    p.region_id = region_id
    p.area_id = area_id
    return p


class _DBStub:
    """SQLAlchemy session stub that hands back the seeded WorkOrder for
    the router's pre-fetch query, the seeded Project for the strategy's
    region/area lookup, and the seeded ProjectAssignment for
    WORK_MANAGER's assignment check."""

    def __init__(self, *, wo=None, project=None, assignment=None):
        self._wo = wo
        self._project = project
        self._assignment = assignment
        self._current_model = None
        self.execute_calls = []

    def query(self, *args):
        # Could be query(WorkOrder), query(Project, Project.region_id)
        # — take the first arg's __name__.
        first = args[0] if args else None
        self._current_model = getattr(first, "__name__", str(first))
        return self

    def filter(self, *a, **kw):
        return self

    def order_by(self, *a, **kw):
        return self

    def first(self):
        if self._current_model == "WorkOrder":
            return self._wo
        if self._current_model == "Project":
            return self._project
        if self._current_model == "ProjectAssignment":
            return self._assignment
        return None

    def all(self):
        return []

    def execute(self, *args, **kwargs):
        self.execute_calls.append(args)
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        cursor.first.return_value = None
        return cursor

    def commit(self):
        return None


# ---------------------------------------------------------------------------
# Mocked service so the auth path is the only thing under test.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _mock_service(monkeypatch):
    """Replace work_order_service so auth-path tests don't hit the DB."""
    fake = MagicMock()
    fake.update.return_value = _wo()
    fake.start.return_value = _wo()
    fake.cancel.return_value = _wo()
    fake.close.return_value = _wo()
    fake.get_work_order.return_value = _wo()
    fake.soft_delete.return_value = None
    monkeypatch.setattr(wo_router, "work_order_service", fake)
    return fake


# Schema mocks — the routers expect WorkOrderUpdate / etc. but our test
# never actually serializes; MagicMock is fine.

def _payload():
    p = MagicMock()
    p.model_dump.return_value = {}
    return p


# ===========================================================================
# 1. update_work_order
# ===========================================================================

class TestUpdateWorkOrderScope:

    def test_admin_passes(self, _mock_service):
        db = _DBStub(wo=_wo(project_id=10), project=_project(region_id=99, area_id=99))
        result = update_work_order(42, _payload(), db, _user("ADMIN"))
        assert result is _mock_service.update.return_value
        _mock_service.update.assert_called_once()

    def test_coordinator_passes(self, _mock_service):
        db = _DBStub(wo=_wo(), project=_project(region_id=99, area_id=99))
        update_work_order(42, _payload(), db, _user("ORDER_COORDINATOR", perms={"work_orders.update"}))
        _mock_service.update.assert_called_once()

    def test_region_manager_in_scope_passes(self, _mock_service):
        db = _DBStub(wo=_wo(), project=_project(region_id=5))
        update_work_order(42, _payload(), db,
                          _user("REGION_MANAGER", perms={"work_orders.update"}, region_id=5))
        _mock_service.update.assert_called_once()

    def test_region_manager_out_of_scope_403(self, _mock_service):
        db = _DBStub(wo=_wo(), project=_project(region_id=99))
        with pytest.raises(HTTPException) as exc:
            update_work_order(42, _payload(), db,
                              _user("REGION_MANAGER", perms={"work_orders.update"}, region_id=5))
        assert exc.value.status_code == 403
        _mock_service.update.assert_not_called()

    def test_area_manager_in_scope_passes(self, _mock_service):
        db = _DBStub(wo=_wo(), project=_project(area_id=12))
        update_work_order(42, _payload(), db,
                          _user("AREA_MANAGER", perms={"work_orders.update"}, area_id=12))
        _mock_service.update.assert_called_once()

    def test_area_manager_out_of_scope_403(self, _mock_service):
        db = _DBStub(wo=_wo(), project=_project(area_id=99))
        with pytest.raises(HTTPException) as exc:
            update_work_order(42, _payload(), db,
                              _user("AREA_MANAGER", perms={"work_orders.update"}, area_id=12))
        assert exc.value.status_code == 403
        _mock_service.update.assert_not_called()

    def test_work_manager_assigned_passes(self, _mock_service):
        assignment = MagicMock(user_id=7, project_id=10, is_active=True)
        db = _DBStub(wo=_wo(project_id=10), assignment=assignment)
        update_work_order(42, _payload(), db,
                          _user("WORK_MANAGER", perms={"work_orders.update"}, user_id=7))
        _mock_service.update.assert_called_once()

    def test_work_manager_unassigned_direct_url_403(self, _mock_service):
        """The leak-closure test: WORK_MANAGER hits PATCH /work-orders/99
        for a WO whose project they're NOT assigned to."""
        db = _DBStub(wo=_wo(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            update_work_order(99, _payload(), db,
                              _user("WORK_MANAGER", perms={"work_orders.update"}, user_id=7))
        assert exc.value.status_code == 403
        _mock_service.update.assert_not_called()

    def test_supplier_403(self, _mock_service):
        db = _DBStub(wo=_wo())
        with pytest.raises(HTTPException) as exc:
            update_work_order(42, _payload(), db,
                              _user("SUPPLIER", perms={"work_orders.update"}))
        assert exc.value.status_code == 403
        _mock_service.update.assert_not_called()

    def test_missing_wo_404(self, _mock_service):
        db = _DBStub(wo=None)
        with pytest.raises(HTTPException) as exc:
            update_work_order(999, _payload(), db, _user("ADMIN"))
        assert exc.value.status_code == 404
        _mock_service.update.assert_not_called()


# ===========================================================================
# 2. delete_work_order
# ===========================================================================

class TestDeleteWorkOrderScope:

    def test_admin_passes(self, _mock_service):
        _mock_service.get_work_order.return_value = _wo()
        db = _DBStub()
        delete_work_order(42, db, _user("ADMIN"))
        _mock_service.soft_delete.assert_called_once()

    def test_supplier_403(self, _mock_service):
        _mock_service.get_work_order.return_value = _wo()
        db = _DBStub()
        with pytest.raises(HTTPException) as exc:
            delete_work_order(42, db, _user("SUPPLIER", perms={"work_orders.delete"}))
        assert exc.value.status_code == 403
        _mock_service.soft_delete.assert_not_called()

    def test_missing_wo_404(self, _mock_service):
        _mock_service.get_work_order.return_value = None
        db = _DBStub()
        with pytest.raises(HTTPException) as exc:
            delete_work_order(999, db, _user("ADMIN"))
        assert exc.value.status_code == 404


# ===========================================================================
# 3. cancel_work_order
# ===========================================================================

class TestCancelWorkOrderScope:

    def test_admin_passes(self, _mock_service):
        db = _DBStub(wo=_wo())
        cancel_work_order(42, db, _user("ADMIN"))
        _mock_service.cancel.assert_called_once()

    def test_region_manager_in_scope_passes(self, _mock_service):
        db = _DBStub(wo=_wo(), project=_project(region_id=5))
        cancel_work_order(42, db,
                          _user("REGION_MANAGER", perms={"work_orders.cancel"}, region_id=5))
        _mock_service.cancel.assert_called_once()

    def test_region_manager_out_of_scope_403(self, _mock_service):
        db = _DBStub(wo=_wo(), project=_project(region_id=99))
        with pytest.raises(HTTPException) as exc:
            cancel_work_order(42, db,
                              _user("REGION_MANAGER", perms={"work_orders.cancel"}, region_id=5))
        assert exc.value.status_code == 403
        _mock_service.cancel.assert_not_called()

    def test_work_manager_unassigned_403(self, _mock_service):
        db = _DBStub(wo=_wo(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            cancel_work_order(99, db,
                              _user("WORK_MANAGER", perms={"work_orders.cancel"}, user_id=7))
        assert exc.value.status_code == 403

    def test_missing_wo_404(self, _mock_service):
        db = _DBStub(wo=None)
        with pytest.raises(HTTPException) as exc:
            cancel_work_order(999, db, _user("ADMIN"))
        assert exc.value.status_code == 404


# ===========================================================================
# 4. close_work_order  (also covers /complete alias which routes here)
# ===========================================================================

class TestCloseWorkOrderScope:

    def test_admin_passes(self, _mock_service):
        db = _DBStub(wo=_wo())
        close_work_order(42, db, _user("ADMIN"), actual_hours=8.0)
        _mock_service.close.assert_called_once()

    def test_area_manager_in_scope_passes(self, _mock_service):
        db = _DBStub(wo=_wo(), project=_project(area_id=12))
        close_work_order(42, db,
                         _user("AREA_MANAGER", perms={"work_orders.close"}, area_id=12))
        _mock_service.close.assert_called_once()

    def test_area_manager_out_of_scope_403(self, _mock_service):
        db = _DBStub(wo=_wo(), project=_project(area_id=99))
        with pytest.raises(HTTPException) as exc:
            close_work_order(42, db,
                             _user("AREA_MANAGER", perms={"work_orders.close"}, area_id=12))
        assert exc.value.status_code == 403
        _mock_service.close.assert_not_called()

    def test_work_manager_unassigned_direct_url_403(self, _mock_service):
        db = _DBStub(wo=_wo(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            close_work_order(99, db,
                             _user("WORK_MANAGER", perms={"work_orders.close"}, user_id=7))
        assert exc.value.status_code == 403

    def test_missing_wo_404(self, _mock_service):
        db = _DBStub(wo=None)
        with pytest.raises(HTTPException) as exc:
            close_work_order(999, db, _user("ADMIN"))
        assert exc.value.status_code == 404


# ===========================================================================
# 5. start_work_order  — the highest-impact migration
# ===========================================================================

class TestStartWorkOrderScope:

    def test_admin_passes(self, _mock_service):
        db = _DBStub(wo=_wo())
        start_work_order(42, db, _user("ADMIN"))
        _mock_service.start.assert_called_once()

    def test_coordinator_passes(self, _mock_service):
        db = _DBStub(wo=_wo())
        start_work_order(42, db, _user("ORDER_COORDINATOR", perms={"work_orders.update"}))
        _mock_service.start.assert_called_once()

    def test_work_manager_assigned_passes(self, _mock_service):
        assignment = MagicMock(user_id=7, project_id=10, is_active=True)
        db = _DBStub(wo=_wo(project_id=10), assignment=assignment)
        start_work_order(42, db,
                         _user("WORK_MANAGER", perms={"work_orders.update"}, user_id=7))
        _mock_service.start.assert_called_once()

    def test_work_manager_unassigned_direct_url_403(self, _mock_service):
        """The flagship leak-closure: WORK_MANAGER /start on a WO they
        don't own. Was 200 before Wave 1.3.a, now 403."""
        db = _DBStub(wo=_wo(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            start_work_order(99, db,
                             _user("WORK_MANAGER", perms={"work_orders.update"}, user_id=7))
        assert exc.value.status_code == 403
        _mock_service.start.assert_not_called()

    def test_region_manager_in_full_region_passes(self, _mock_service):
        """Sanity: REGION_MANAGER sees the full region, not just one
        area. A WO on a project in their region but in a *different*
        area than the user's area_id still passes."""
        db = _DBStub(wo=_wo(), project=_project(region_id=5, area_id=999))
        start_work_order(42, db,
                         _user("REGION_MANAGER", perms={"work_orders.update"},
                               region_id=5, area_id=12))
        _mock_service.start.assert_called_once()

    def test_region_manager_out_of_region_403(self, _mock_service):
        db = _DBStub(wo=_wo(), project=_project(region_id=99))
        with pytest.raises(HTTPException) as exc:
            start_work_order(42, db,
                             _user("REGION_MANAGER", perms={"work_orders.update"}, region_id=5))
        assert exc.value.status_code == 403

    def test_supplier_403(self, _mock_service):
        db = _DBStub(wo=_wo())
        with pytest.raises(HTTPException) as exc:
            start_work_order(42, db, _user("SUPPLIER", perms={"work_orders.update"}))
        assert exc.value.status_code == 403

    def test_missing_wo_404(self, _mock_service):
        db = _DBStub(wo=None)
        with pytest.raises(HTTPException) as exc:
            start_work_order(999, db, _user("ADMIN"))
        assert exc.value.status_code == 404
