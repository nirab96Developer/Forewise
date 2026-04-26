"""
Phase 3 Wave 3.1.6.b — defense-in-depth scope check on
worklog approve / reject.

Today's reality (per recon):
  - Only ADMIN holds `worklogs.approve` in DB; everyone else lacks
    it and is blocked by `require_permission` before they ever
    reach the strategy.
  - AREA / REGION / WORK_MANAGER hold `worklogs.reject` in DB, but
    the router checks `worklogs.approve` — that grant is currently
    dead code. We do NOT fix that in this wave (out of scope).

What this wave adds:
  - fetch the worklog and 404 if missing
  - call AuthorizationService.authorize(... "Worklog")
  - placed BEFORE the try/except so HTTPException(403/404)
    doesn't get swallowed into 500.

Behavior preservation
---------------------
ADMIN keeps approving/rejecting anything — confirmed by tests.
SUPPLIER / ACCOUNTANT / AREA_MGR / REGION_MGR / WORK_MGR keep
getting 403 because they lack the perm — confirmed.

Future-proofing
---------------
The regression test below grants a non-admin role the
`worklogs.approve` perm in-memory. Without the strategy migration
this would let them approve any worklog system-wide. With the
strategy, they pass for in-scope and 403 for out-of-scope.
That's the actual "defense in depth" payoff.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.worklogs import approve_worklog, reject_worklog
from app.routers import worklogs as wl_router
from app.schemas.worklog import WorklogActionBody


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(role_code, *, perms=None, user_id=1, region_id=None, area_id=None):
    user = MagicMock()
    user.id = user_id
    user.role_id = 1
    user.is_active = True
    user.region_id = region_id
    user.area_id = area_id
    user.full_name = f"User {user_id}"
    user.username = f"user_{user_id}"
    user.email = "x@example.com"
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = [MagicMock(code=p) for p in (perms or set())]
    user._permissions = set(perms or set())
    return user


def _worklog(*, wl_id=42, project_id=10, user_id=1):
    w = MagicMock()
    w.id = wl_id
    w.project_id = project_id
    w.user_id = user_id
    w.work_order_id = None
    w.status = "SUBMITTED"
    w.report_number = wl_id
    w.report_date = None
    w.equipment_type = ""
    w.total_hours = 0
    w.paid_hours = 0
    w.net_hours = 0
    w.start_time = None
    w.end_time = None
    w.notes = ""
    w.approved_at = None
    w.is_standard = True
    return w


def _project(*, project_id=10, region_id=None, area_id=None):
    p = MagicMock()
    p.id = project_id
    p.region_id = region_id
    p.area_id = area_id
    return p


class _DBStub:
    def __init__(self, *, worklog=None, project=None, assignment=None):
        self._worklog = worklog
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
        if self._current_model == "Worklog":
            return self._worklog
        if self._current_model == "Project":
            return self._project
        if self._current_model == "ProjectAssignment":
            return self._assignment
        if self._current_model == "WorkOrder":
            return None
        return None

    def all(self):
        return []

    def subquery(self):
        return self


@pytest.fixture(autouse=True)
def _mock_service(monkeypatch):
    """Mock the worklog_service so approve / reject don't need a real
    DB row. Notifications are stubbed too."""
    fake = MagicMock()
    fake.approve.return_value = _worklog(wl_id=42)
    fake.reject.return_value = _worklog(wl_id=42)
    monkeypatch.setattr(wl_router, "worklog_service", fake)
    monkeypatch.setattr(wl_router, "notify_worklog_approved", lambda *a, **k: None)
    monkeypatch.setattr(wl_router, "notify_worklog_rejected", lambda *a, **k: None)
    return fake


# ===========================================================================
# Approve — production roles
# ===========================================================================

class TestApproveProductionRoles:
    """Pin today's behavior: only ADMIN can approve. Wave didn't
    change who's allowed."""

    # Helper: when calling these handlers as plain Python functions
    # (not via FastAPI), the `body=Body(default=None)` and
    # `notes=Query(default=None)` defaults stay as wrapper objects,
    # not None. We pass body=None / notes=None explicitly.
    _APPROVE_KW = {"body": None, "notes": None}

    def test_admin_passes(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        approve_worklog(42, db, _user("ADMIN"), **self._APPROVE_KW)
        _mock_service.approve.assert_called_once()

    def test_area_manager_blocked_by_perm_403(self, _mock_service):
        """AREA_MGR has worklogs.reject in DB but NOT worklogs.approve.
        The router checks approve → 403 before reaching the strategy."""
        db = _DBStub(worklog=_worklog())
        with pytest.raises(HTTPException) as exc:
            approve_worklog(
                42, db,
                _user("AREA_MANAGER", perms={"worklogs.read", "worklogs.reject"}),
                **self._APPROVE_KW,
            )
        assert exc.value.status_code == 403
        _mock_service.approve.assert_not_called()

    def test_region_manager_blocked_by_perm_403(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        with pytest.raises(HTTPException) as exc:
            approve_worklog(
                42, db,
                _user("REGION_MANAGER", perms={"worklogs.read", "worklogs.reject"}),
                **self._APPROVE_KW,
            )
        assert exc.value.status_code == 403

    def test_work_manager_blocked_by_perm_403(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        with pytest.raises(HTTPException) as exc:
            approve_worklog(
                42, db,
                _user("WORK_MANAGER", perms={"worklogs.read", "worklogs.reject"}),
                **self._APPROVE_KW,
            )
        assert exc.value.status_code == 403

    def test_accountant_blocked_by_perm_403(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        with pytest.raises(HTTPException) as exc:
            approve_worklog(
                42, db,
                _user("ACCOUNTANT", perms={"worklogs.read"}),
                **self._APPROVE_KW,
            )
        assert exc.value.status_code == 403

    def test_supplier_blocked_by_perm_403(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        with pytest.raises(HTTPException) as exc:
            approve_worklog(
                42, db,
                _user("SUPPLIER", perms={"worklogs.read_own", "worklogs.submit"}),
                **self._APPROVE_KW,
            )
        assert exc.value.status_code == 403

    def test_field_worker_blocked_by_perm_403(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        with pytest.raises(HTTPException) as exc:
            approve_worklog(
                42, db, _user("FIELD_WORKER", perms=set()),
                **self._APPROVE_KW,
            )
        assert exc.value.status_code == 403

    def test_missing_worklog_404(self, _mock_service):
        db = _DBStub(worklog=None)
        with pytest.raises(HTTPException) as exc:
            approve_worklog(999, db, _user("ADMIN"), **self._APPROVE_KW)
        assert exc.value.status_code == 404


# ===========================================================================
# Reject — production roles
# ===========================================================================

class TestRejectProductionRoles:

    def _payload(self):
        return WorklogActionBody(rejection_reason="bad data")

    def test_admin_passes(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        reject_worklog(42, db, _user("ADMIN"), body=self._payload())
        _mock_service.reject.assert_called_once()

    def test_area_manager_blocked_by_perm_403(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        with pytest.raises(HTTPException) as exc:
            reject_worklog(
                42, db,
                _user("AREA_MANAGER", perms={"worklogs.read", "worklogs.reject"}),
                body=self._payload(),
            )
        assert exc.value.status_code == 403

    def test_region_manager_blocked_by_perm_403(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        with pytest.raises(HTTPException) as exc:
            reject_worklog(
                42, db,
                _user("REGION_MANAGER", perms={"worklogs.read", "worklogs.reject"}),
                body=self._payload(),
            )
        assert exc.value.status_code == 403

    def test_supplier_blocked_by_perm_403(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        with pytest.raises(HTTPException) as exc:
            reject_worklog(
                42, db,
                _user("SUPPLIER", perms={"worklogs.read_own"}),
                body=self._payload(),
            )
        assert exc.value.status_code == 403

    def test_missing_worklog_404(self, _mock_service):
        db = _DBStub(worklog=None)
        with pytest.raises(HTTPException) as exc:
            reject_worklog(999, db, _user("ADMIN"), body=self._payload())
        assert exc.value.status_code == 404

    def test_admin_missing_reason_422(self, _mock_service):
        """Reason validation (422) STILL happens after auth — pin it."""
        db = _DBStub(worklog=_worklog())
        with pytest.raises(HTTPException) as exc:
            reject_worklog(
                42, db, _user("ADMIN"),
                body=None,
                rejection_reason=None,
            )
        assert exc.value.status_code == 422


# ===========================================================================
# Defense-in-depth regression: prove the strategy is wired
# ===========================================================================

class TestStrategyIsWiredForFutureGrants:
    """The whole point of this wave: if a non-admin role is later
    granted `worklogs.approve`, the strategy MUST kick in. These
    tests grant the perm explicitly in-memory and verify the
    strategy enforces scope.

    This is what makes Wave 3.1.6.b 'defense in depth' rather than
    a no-op refactor."""

    _KW = {"body": None, "notes": None}

    def test_area_manager_with_approve_perm_in_scope_passes(self, _mock_service):
        """If product later grants AREA_MGR worklogs.approve, they
        should approve worklogs in their area."""
        db = _DBStub(worklog=_worklog(), project=_project(area_id=12))
        approve_worklog(
            42, db,
            _user("AREA_MANAGER", perms={"worklogs.approve"}, area_id=12),
            **self._KW,
        )
        _mock_service.approve.assert_called_once()

    def test_area_manager_with_approve_perm_out_of_scope_403(self, _mock_service):
        """And the strategy STOPS them on out-of-scope worklogs.
        This is the regression test for the leak that would exist
        WITHOUT this wave — a future perm grant would silently let
        AREA_MGR approve other regions."""
        db = _DBStub(worklog=_worklog(), project=_project(area_id=99))
        with pytest.raises(HTTPException) as exc:
            approve_worklog(
                42, db,
                _user("AREA_MANAGER", perms={"worklogs.approve"}, area_id=12),
                **self._KW,
            )
        assert exc.value.status_code == 403
        _mock_service.approve.assert_not_called()

    def test_region_manager_with_approve_perm_in_scope_passes(self, _mock_service):
        db = _DBStub(worklog=_worklog(), project=_project(region_id=5))
        approve_worklog(
            42, db,
            _user("REGION_MANAGER", perms={"worklogs.approve"}, region_id=5),
            **self._KW,
        )
        _mock_service.approve.assert_called_once()

    def test_region_manager_with_approve_perm_out_of_scope_403(self, _mock_service):
        db = _DBStub(worklog=_worklog(), project=_project(region_id=99))
        with pytest.raises(HTTPException) as exc:
            approve_worklog(
                42, db,
                _user("REGION_MANAGER", perms={"worklogs.approve"}, region_id=5),
                **self._KW,
            )
        assert exc.value.status_code == 403

    def test_work_manager_with_approve_perm_unassigned_403(self, _mock_service):
        """WORK_MANAGER with the perm: in-scope = assigned; out-of-scope
        (URL probing for a project they don't own) → 403."""
        db = _DBStub(worklog=_worklog(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            approve_worklog(
                99, db,
                _user("WORK_MANAGER", perms={"worklogs.approve"}, user_id=7),
                **self._KW,
            )
        assert exc.value.status_code == 403

    def test_work_manager_with_approve_perm_assigned_passes(self, _mock_service):
        assignment = MagicMock(user_id=7, project_id=10, is_active=True)
        db = _DBStub(worklog=_worklog(project_id=10), assignment=assignment)
        approve_worklog(
            42, db,
            _user("WORK_MANAGER", perms={"worklogs.approve"}, user_id=7),
            **self._KW,
        )
        _mock_service.approve.assert_called_once()

    def test_supplier_with_approve_perm_still_blocked_by_strategy(self, _mock_service):
        """A SUPPLIER given approve perm by mistake (e.g. wrong DB
        seed) STILL can't approve someone else's worklog — the
        OWN_ONLY branch of the strategy denies cross-user access."""
        db = _DBStub(worklog=_worklog(user_id=999))
        with pytest.raises(HTTPException) as exc:
            approve_worklog(
                42, db,
                _user("SUPPLIER", perms={"worklogs.approve"}, user_id=42),
                **self._KW,
            )
        assert exc.value.status_code == 403
