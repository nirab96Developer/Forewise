"""
Phase 3 Wave 3.1.6.c — scope enforcement on worklog state-mutation
endpoints (submit, update, delete, activate).

Per the recon, these endpoints split into two patterns:

  submit (`POST /worklogs/{id}/submit`)
    Owner-bypass: an owner submits their own report self-service —
    no perm, no scope check. This is preserved EXACTLY.
    Non-owner: keeps the existing `worklogs.submit` perm gate, plus
    a new scope check via the strategy.

  update / delete / activate
    Today only ADMIN holds the relevant perm; the strategy is a
    no-op for the sole caller. Tests pin today's behavior, plus
    regression cases that demonstrate the strategy is wired for
    future perm grants.

The scan-gate logic in submit (workorder status validation +
equipment-scan-required check) is NOT tested here — it's exercised
by tests/test_worklogs_crud.py against a live DB. We verify
ONLY that the auth pipeline behavior is correct.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.worklogs import (
    submit_worklog,
    update_worklog,
    delete_worklog,
    activate_worklog,
)
from app.routers import worklogs as wl_router
from app.schemas.worklog import WorklogActionBody, WorklogUpdate


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


def _worklog(*, wl_id=42, project_id=10, user_id=1, work_order_id=None,
              report_date=None):
    w = MagicMock()
    w.id = wl_id
    w.project_id = project_id
    w.user_id = user_id
    w.work_order_id = work_order_id
    w.status = "DRAFT"
    w.report_number = wl_id
    w.report_date = report_date
    w.equipment_scanned = False
    w.scan_time = None
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

    def execute(self, *a, **kw):
        cursor = MagicMock()
        cursor.scalar.return_value = 1  # for scan-gate stub
        return cursor

    def subquery(self):
        return self


@pytest.fixture(autouse=True)
def _mock_service(monkeypatch):
    """Replace worklog_service so handlers don't hit the DB."""
    fake = MagicMock()
    fake.get_by_id.side_effect = lambda db, wid: getattr(db, "_worklog", None)
    fake.submit.return_value = _worklog()
    fake.update.return_value = _worklog()
    fake.deactivate.return_value = None
    fake.activate.return_value = _worklog()
    monkeypatch.setattr(wl_router, "worklog_service", fake)
    monkeypatch.setattr(wl_router, "notify_worklog_created", lambda *a, **k: None)
    return fake


# ===========================================================================
# 1. submit — owner-bypass + non-owner perm+scope
# ===========================================================================

class TestSubmitOwnerBypass:
    """Pin the owner-bypass behavior — owner submits their own report
    without perm or scope check. Critical: this is a self-service
    flow we MUST NOT break."""

    _KW = {"body": None, "notes": None}

    def test_supplier_owner_submits_own_passes(self, _mock_service):
        """SUPPLIER (no work_orders.submit) submitting their own
        worklog should succeed via the owner-bypass path."""
        wl = _worklog(user_id=42, work_order_id=None)
        db = _DBStub(worklog=wl)
        result = submit_worklog(
            42, db, _user("SUPPLIER", perms=set(), user_id=42),
            **self._KW,
        )
        _mock_service.submit.assert_called_once()

    def test_field_worker_owner_submits_own_passes(self, _mock_service):
        wl = _worklog(user_id=99, work_order_id=None)
        db = _DBStub(worklog=wl)
        submit_worklog(
            42, db, _user("FIELD_WORKER", perms=set(), user_id=99),
            **self._KW,
        )
        _mock_service.submit.assert_called_once()

    def test_admin_passes(self, _mock_service):
        wl = _worklog(user_id=999, work_order_id=None)  # not admin's own
        db = _DBStub(worklog=wl)
        submit_worklog(42, db, _user("ADMIN"), **self._KW)
        _mock_service.submit.assert_called_once()


class TestSubmitNonOwner:
    """Non-owner needs the perm + scope. Owner-bypass is preserved."""

    _KW = {"body": None, "notes": None}

    def test_non_owner_without_perm_403(self, _mock_service):
        wl = _worklog(user_id=999, work_order_id=None)
        db = _DBStub(worklog=wl)
        with pytest.raises(HTTPException) as exc:
            submit_worklog(
                42, db, _user("WORK_MANAGER", perms=set(), user_id=42),
                **self._KW,
            )
        assert exc.value.status_code == 403
        _mock_service.submit.assert_not_called()

    def test_non_owner_with_perm_in_scope_passes(self, _mock_service):
        """Future-grant regression: WORK_MGR with worklogs.submit on
        a worklog in their assigned project."""
        wl = _worklog(user_id=999, project_id=10, work_order_id=None)
        assignment = MagicMock(user_id=42, project_id=10, is_active=True)
        db = _DBStub(worklog=wl, assignment=assignment)
        submit_worklog(
            42, db,
            _user("WORK_MANAGER", perms={"worklogs.submit"}, user_id=42),
            **self._KW,
        )
        _mock_service.submit.assert_called_once()

    def test_non_owner_with_perm_out_of_scope_403(self, _mock_service):
        """Future-grant regression: WORK_MGR with worklogs.submit
        but worklog is on an unassigned project → strategy denies."""
        wl = _worklog(user_id=999, project_id=99, work_order_id=None)
        db = _DBStub(worklog=wl, assignment=None)
        with pytest.raises(HTTPException) as exc:
            submit_worklog(
                99, db,
                _user("WORK_MANAGER", perms={"worklogs.submit"}, user_id=42),
                **self._KW,
            )
        assert exc.value.status_code == 403

    def test_supplier_with_perm_other_user_403(self, _mock_service):
        """SUPPLIER holds worklogs.submit in DB. They CAN submit their
        own. They CANNOT submit someone else's — OWN_ONLY branch
        denies."""
        wl = _worklog(user_id=999, work_order_id=None)
        db = _DBStub(worklog=wl)
        with pytest.raises(HTTPException) as exc:
            submit_worklog(
                42, db,
                _user("SUPPLIER", perms={"worklogs.submit"}, user_id=42),
                **self._KW,
            )
        assert exc.value.status_code == 403


class TestSubmitMissing:

    def test_missing_worklog_404(self, _mock_service):
        db = _DBStub(worklog=None)
        with pytest.raises(HTTPException) as exc:
            submit_worklog(999, db, _user("ADMIN"), body=None, notes=None)
        assert exc.value.status_code == 404


# ===========================================================================
# 2. update — defense-in-depth
# ===========================================================================

class TestUpdateProductionRoles:
    """Today only ADMIN holds worklogs.update. Pin that."""

    def test_admin_passes(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        update_worklog(42, WorklogUpdate(), db, _user("ADMIN"))
        _mock_service.update.assert_called_once()

    def test_supplier_blocked_by_perm_403(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        with pytest.raises(HTTPException) as exc:
            update_worklog(
                42, WorklogUpdate(), db,
                _user("SUPPLIER", perms={"worklogs.read_own"}, user_id=42),
            )
        assert exc.value.status_code == 403

    def test_field_worker_blocked_by_perm_403(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        with pytest.raises(HTTPException) as exc:
            update_worklog(
                42, WorklogUpdate(), db,
                _user("FIELD_WORKER", perms=set(), user_id=42),
            )
        assert exc.value.status_code == 403

    def test_missing_worklog_404(self, _mock_service):
        db = _DBStub(worklog=None)
        with pytest.raises(HTTPException) as exc:
            update_worklog(999, WorklogUpdate(), db, _user("ADMIN"))
        assert exc.value.status_code == 404


class TestUpdateStrategyWiredForFutureGrants:

    def test_area_manager_with_perm_in_scope_passes(self, _mock_service):
        db = _DBStub(worklog=_worklog(), project=_project(area_id=12))
        update_worklog(
            42, WorklogUpdate(), db,
            _user("AREA_MANAGER", perms={"worklogs.update"}, area_id=12),
        )
        _mock_service.update.assert_called_once()

    def test_area_manager_with_perm_out_of_scope_403(self, _mock_service):
        db = _DBStub(worklog=_worklog(), project=_project(area_id=99))
        with pytest.raises(HTTPException) as exc:
            update_worklog(
                42, WorklogUpdate(), db,
                _user("AREA_MANAGER", perms={"worklogs.update"}, area_id=12),
            )
        assert exc.value.status_code == 403

    def test_work_manager_with_perm_unassigned_403(self, _mock_service):
        db = _DBStub(worklog=_worklog(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            update_worklog(
                99, WorklogUpdate(), db,
                _user("WORK_MANAGER", perms={"worklogs.update"}, user_id=7),
            )
        assert exc.value.status_code == 403

    def test_supplier_with_perm_own_passes(self, _mock_service):
        """If product later grants SUPPLIER worklogs.update, the
        strategy's OWN_ONLY branch lets them update their own
        worklog (and only their own)."""
        wl = _worklog(user_id=42)
        db = _DBStub(worklog=wl)
        update_worklog(
            42, WorklogUpdate(), db,
            _user("SUPPLIER", perms={"worklogs.update"}, user_id=42),
        )
        _mock_service.update.assert_called_once()

    def test_supplier_with_perm_other_user_403(self, _mock_service):
        wl = _worklog(user_id=999)
        db = _DBStub(worklog=wl)
        with pytest.raises(HTTPException) as exc:
            update_worklog(
                42, WorklogUpdate(), db,
                _user("SUPPLIER", perms={"worklogs.update"}, user_id=42),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# 3. delete — admin-only
# ===========================================================================

class TestDelete:

    def test_admin_passes(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        delete_worklog(42, db, _user("ADMIN"))
        _mock_service.deactivate.assert_called_once()

    def test_supplier_blocked_403(self, _mock_service):
        db = _DBStub(worklog=_worklog(user_id=42))
        with pytest.raises(HTTPException) as exc:
            delete_worklog(
                42, db, _user("SUPPLIER", perms={"worklogs.read_own"}, user_id=42),
            )
        assert exc.value.status_code == 403

    def test_area_manager_blocked_403(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        with pytest.raises(HTTPException) as exc:
            delete_worklog(
                42, db, _user("AREA_MANAGER", perms={"worklogs.read"}),
            )
        assert exc.value.status_code == 403

    def test_missing_worklog_404(self, _mock_service):
        db = _DBStub(worklog=None)
        with pytest.raises(HTTPException) as exc:
            delete_worklog(999, db, _user("ADMIN"))
        assert exc.value.status_code == 404

    def test_strategy_blocks_supplier_with_delete_perm_on_other_user(self, _mock_service):
        """Defense-in-depth: a SUPPLIER given worklogs.delete by
        mistake STILL can't delete someone else's worklog."""
        db = _DBStub(worklog=_worklog(user_id=999))
        with pytest.raises(HTTPException) as exc:
            delete_worklog(
                42, db,
                _user("SUPPLIER", perms={"worklogs.delete"}, user_id=42),
            )
        assert exc.value.status_code == 403


# ===========================================================================
# 4. activate — admin-only
# ===========================================================================

class TestActivate:

    def test_admin_passes(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        activate_worklog(42, db, _user("ADMIN"))
        _mock_service.activate.assert_called_once()

    def test_non_admin_blocked_403(self, _mock_service):
        db = _DBStub(worklog=_worklog())
        with pytest.raises(HTTPException) as exc:
            activate_worklog(
                42, db, _user("AREA_MANAGER", perms={"worklogs.read"}),
            )
        assert exc.value.status_code == 403

    def test_supplier_blocked_403(self, _mock_service):
        db = _DBStub(worklog=_worklog(user_id=42))
        with pytest.raises(HTTPException) as exc:
            activate_worklog(
                42, db,
                _user("SUPPLIER", perms={"worklogs.read_own"}, user_id=42),
            )
        assert exc.value.status_code == 403

    def test_missing_worklog_404(self, _mock_service):
        db = _DBStub(worklog=None)
        with pytest.raises(HTTPException) as exc:
            activate_worklog(999, db, _user("ADMIN"))
        assert exc.value.status_code == 404
