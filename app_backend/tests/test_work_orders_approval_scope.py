"""
Phase 3 Wave 1.3.c — defense-in-depth scope check on approve/reject.

These two endpoints are the most behaviorally-conservative migration
of the whole sub-wave: the existing
`_require_order_coordinator_or_admin` wrapper already restricts to
ADMIN / SUPER_ADMIN / ORDER_COORDINATOR. All three are in the
WorkOrderScopeStrategy GLOBAL_ROLES set, so calling `authorize` on
top is a no-op for them and behavior is preserved exactly.

What the new check buys: if the queue wrapper is ever loosened (or
removed) for product reasons — for example, if AREA_MGR is later
allowed to approve in their own area — the strategy will still
enforce scope. This sub-wave doesn't change who can approve/reject;
it just removes the latent risk that someone removes the wrapper
without thinking through scope.

Tests assert the existing 403 boundaries are unchanged for non-coord
roles, plus standard auth-pipeline tests.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.work_orders import (
    approve_work_order,
    reject_work_order,
)
from app.routers import work_orders as wo_router
from app.schemas.work_order import WorkOrderApproveRequest, WorkOrderRejectRequest


# ---------------------------------------------------------------------------
# Test helpers (same shape as 1.3.a / 1.3.b)
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
    def __init__(self, *, wo=None, project=None, assignment=None):
        self._wo = wo
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
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        return cursor

    def commit(self):
        return None


@pytest.fixture(autouse=True)
def _mock_service(monkeypatch):
    fake = MagicMock()
    fake.approve.return_value = _wo(status="APPROVED_AND_SENT")
    fake.reject.return_value = _wo(status="REJECTED")
    monkeypatch.setattr(wo_router, "work_order_service", fake)

    # Notifications are best-effort and hit DB — stub them out.
    monkeypatch.setattr(wo_router, "notify_work_order_approved", lambda *a, **k: None)
    monkeypatch.setattr(wo_router, "notify_work_order_rejected", lambda *a, **k: None)
    return fake


# ===========================================================================
# 1. approve_work_order
# ===========================================================================

class TestApproveWorkOrder:

    def test_admin_passes(self, _mock_service):
        db = _DBStub(wo=_wo())
        approve_work_order(42, db, _user("ADMIN"), WorkOrderApproveRequest())
        _mock_service.approve.assert_called_once()

    def test_coordinator_passes(self, _mock_service):
        db = _DBStub(wo=_wo())
        approve_work_order(
            42, db,
            _user("ORDER_COORDINATOR", perms={"work_orders.approve"}),
            WorkOrderApproveRequest(),
        )
        _mock_service.approve.assert_called_once()

    # The four roles below all hold work_orders.approve in DB but are
    # blocked by _require_order_coordinator_or_admin. These tests pin
    # that behavior — ensures Wave 1.3.c didn't accidentally relax it.

    def test_region_manager_blocked_by_queue_wrapper_403(self, _mock_service):
        db = _DBStub(wo=_wo(), project=_project(region_id=5))
        with pytest.raises(HTTPException) as exc:
            approve_work_order(
                42, db,
                _user("REGION_MANAGER", perms={"work_orders.approve"}, region_id=5),
                WorkOrderApproveRequest(),
            )
        assert exc.value.status_code == 403
        _mock_service.approve.assert_not_called()

    def test_area_manager_blocked_by_queue_wrapper_403(self, _mock_service):
        db = _DBStub(wo=_wo(), project=_project(area_id=12))
        with pytest.raises(HTTPException) as exc:
            approve_work_order(
                42, db,
                _user("AREA_MANAGER", perms={"work_orders.approve"}, area_id=12),
                WorkOrderApproveRequest(),
            )
        assert exc.value.status_code == 403

    def test_work_manager_blocked_by_queue_wrapper_403(self, _mock_service):
        assignment = MagicMock(user_id=7, project_id=10, is_active=True)
        db = _DBStub(wo=_wo(project_id=10), assignment=assignment)
        with pytest.raises(HTTPException) as exc:
            approve_work_order(
                42, db,
                _user("WORK_MANAGER", perms={"work_orders.approve"}, user_id=7),
                WorkOrderApproveRequest(),
            )
        assert exc.value.status_code == 403

    def test_accountant_blocked_403(self, _mock_service):
        db = _DBStub(wo=_wo())
        with pytest.raises(HTTPException) as exc:
            approve_work_order(
                42, db,
                _user("ACCOUNTANT", perms={"work_orders.read"}),
                WorkOrderApproveRequest(),
            )
        # Either the perm gate (ACCOUNTANT lacks work_orders.approve)
        # or the queue wrapper will fire — both yield 403.
        assert exc.value.status_code == 403

    def test_supplier_blocked_403(self, _mock_service):
        db = _DBStub(wo=_wo())
        with pytest.raises(HTTPException) as exc:
            approve_work_order(
                42, db,
                _user("SUPPLIER", perms={"work_orders.read_own"}),
                WorkOrderApproveRequest(),
            )
        assert exc.value.status_code == 403

    def test_missing_wo_404(self, _mock_service):
        """Coordinator/admin pass perm + queue gate, then hit 404 on
        the new fetch. Pre-1.3.c the service raised 404 too — same UX."""
        db = _DBStub(wo=None)
        with pytest.raises(HTTPException) as exc:
            approve_work_order(
                999, db,
                _user("ORDER_COORDINATOR", perms={"work_orders.approve"}),
                WorkOrderApproveRequest(),
            )
        assert exc.value.status_code == 404


# ===========================================================================
# 2. reject_work_order
# ===========================================================================

class TestRejectWorkOrder:

    def _payload(self):
        return WorkOrderRejectRequest(reason="some reason", notes="")

    def test_admin_passes(self, _mock_service):
        db = _DBStub(wo=_wo())
        reject_work_order(42, self._payload(), db, _user("ADMIN"))
        _mock_service.reject.assert_called_once()

    def test_coordinator_passes(self, _mock_service):
        db = _DBStub(wo=_wo())
        reject_work_order(
            42, self._payload(), db,
            _user("ORDER_COORDINATOR", perms={"work_orders.approve"}),
        )
        _mock_service.reject.assert_called_once()

    def test_region_manager_blocked_403(self, _mock_service):
        db = _DBStub(wo=_wo(), project=_project(region_id=5))
        with pytest.raises(HTTPException) as exc:
            reject_work_order(
                42, self._payload(), db,
                _user("REGION_MANAGER", perms={"work_orders.approve"}, region_id=5),
            )
        assert exc.value.status_code == 403
        _mock_service.reject.assert_not_called()

    def test_area_manager_blocked_403(self, _mock_service):
        db = _DBStub(wo=_wo(), project=_project(area_id=12))
        with pytest.raises(HTTPException) as exc:
            reject_work_order(
                42, self._payload(), db,
                _user("AREA_MANAGER", perms={"work_orders.approve"}, area_id=12),
            )
        assert exc.value.status_code == 403

    def test_work_manager_blocked_403(self, _mock_service):
        db = _DBStub(wo=_wo(project_id=10),
                     assignment=MagicMock(user_id=7, project_id=10, is_active=True))
        with pytest.raises(HTTPException) as exc:
            reject_work_order(
                42, self._payload(), db,
                _user("WORK_MANAGER", perms={"work_orders.approve"}, user_id=7),
            )
        assert exc.value.status_code == 403

    def test_accountant_blocked_403(self, _mock_service):
        db = _DBStub(wo=_wo())
        with pytest.raises(HTTPException) as exc:
            reject_work_order(
                42, self._payload(), db,
                _user("ACCOUNTANT", perms={"work_orders.read"}),
            )
        assert exc.value.status_code == 403

    def test_supplier_blocked_403(self, _mock_service):
        db = _DBStub(wo=_wo())
        with pytest.raises(HTTPException) as exc:
            reject_work_order(
                42, self._payload(), db,
                _user("SUPPLIER", perms={"work_orders.read_own"}),
            )
        assert exc.value.status_code == 403

    def test_missing_wo_404(self, _mock_service):
        db = _DBStub(wo=None)
        with pytest.raises(HTTPException) as exc:
            reject_work_order(
                999, self._payload(), db,
                _user("ORDER_COORDINATOR", perms={"work_orders.approve"}),
            )
        assert exc.value.status_code == 404
