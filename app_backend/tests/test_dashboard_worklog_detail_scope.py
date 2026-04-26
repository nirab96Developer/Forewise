"""
Phase 3 Wave 2.2.a — scope enforcement on
GET /dashboard/worklog-detail/{worklog_id}.

Closes leak D1 from PHASE3_WAVE22_RECON.md: any caller with
`dashboard.view` could fetch ANY worklog's financial fields
(hourly_rate, cost_with_vat, cost_before_vat, audit trail,
supplier name) by guessing the worklog ID. Same shape as the
Worklog PDF leak closed in Wave 3.1.6.a.

The fix wires the existing WorklogScopeStrategy via
AuthorizationService BEFORE the raw SQL fetch. Behavior is
preserved for the intended callers (ADMIN, ACCOUNTANT) since
they're in WorklogScopeStrategy.GLOBAL_ROLES.
"""
import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.dashboard import get_worklog_detail
from app.routers import dashboard as dash_router


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
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = [MagicMock(code=p) for p in (perms or set())]
    user._permissions = set(perms or set())
    return user


def _worklog(*, wl_id=42, project_id=10, user_id=1, work_order_id=None):
    w = MagicMock()
    w.id = wl_id
    w.project_id = project_id
    w.user_id = user_id
    w.work_order_id = work_order_id
    w.status = "SUBMITTED"
    w.report_number = wl_id
    return w


def _project(*, project_id=10, region_id=None, area_id=None):
    p = MagicMock()
    p.id = project_id
    p.region_id = region_id
    p.area_id = area_id
    return p


class _DBStub:
    """Stub that returns:
      - the seeded worklog for `db.query(Worklog).filter(...).first()`
      - the seeded project for `db.query(Project).filter(...).first()`
        (used by WorklogScopeStrategy._project_for)
      - the seeded assignment for ProjectAssignment lookups (WORK_MGR)
      - the seeded raw row for the existing dashboard SQL (when auth
        passes — only matters for happy-path tests).
    """

    def __init__(self, *, worklog=None, project=None, assignment=None, raw_row=None):
        self._worklog = worklog
        self._project = project
        self._assignment = assignment
        self._raw_row = raw_row or _raw_row()
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

    def execute(self, *args, **kwargs):
        cursor = MagicMock()
        # The dashboard does multiple .first() and .fetchall() calls
        # for project/supplier/audit lookups. Hand back the seeded
        # raw row for the worklog query, empty for everything else.
        cursor.first.return_value = self._raw_row
        cursor.fetchall.return_value = []
        return cursor


def _raw_row():
    """Mock the SQLAlchemy Row tuple that the dashboard expects."""
    row = MagicMock()
    # 30-element tuple — kept simple via __getitem__
    values = [
        42, 100, "2026-04-26", "standard", "SUBMITTED",
        9.0, 1.5, 9.0, 9.0,
        100.0, "system_rate", 900.0, 1062.0,
        False, 0, 0.0, 0.0,
        True, "tractor", "ok",
        None, 0.18,
        "Project X", "Supplier Y", "Reporter Z",
        None,
        "1234567", "Tractor 1", "TR-1",
        "WO-100",
    ]
    row.__getitem__.side_effect = lambda i: values[i]
    return row


# ===========================================================================
# Auth gate behavior
# ===========================================================================

class TestWorklogDetailScope:

    def test_admin_passes(self):
        db = _DBStub(worklog=_worklog())
        result = asyncio.run(get_worklog_detail(
            worklog_id=42, db=db, current_user=_user("ADMIN"),
        ))
        assert result["id"] == 42
        assert result["cost_with_vat"] == 1062.0  # financial field present

    def test_accountant_passes(self):
        """Accountant is the intended audience for this endpoint."""
        db = _DBStub(worklog=_worklog())
        result = asyncio.run(get_worklog_detail(
            worklog_id=42, db=db,
            current_user=_user("ACCOUNTANT", perms={"dashboard.view"}),
        ))
        assert result["id"] == 42

    def test_coordinator_passes(self):
        """COORDINATOR is in GLOBAL_ROLES — passes."""
        db = _DBStub(worklog=_worklog())
        result = asyncio.run(get_worklog_detail(
            worklog_id=42, db=db,
            current_user=_user("ORDER_COORDINATOR", perms={"dashboard.view"}),
        ))
        assert result["id"] == 42

    def test_region_manager_in_region_passes(self):
        db = _DBStub(
            worklog=_worklog(),
            project=_project(region_id=5),
        )
        result = asyncio.run(get_worklog_detail(
            worklog_id=42, db=db,
            current_user=_user("REGION_MANAGER",
                               perms={"dashboard.view"}, region_id=5),
        ))
        assert result["id"] == 42

    def test_region_manager_out_of_region_403(self):
        """Flagship leak-closure: REGION_MANAGER can't pull a
        worklog detail from a different region."""
        db = _DBStub(
            worklog=_worklog(),
            project=_project(region_id=99),
        )
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_worklog_detail(
                worklog_id=42, db=db,
                current_user=_user("REGION_MANAGER",
                                   perms={"dashboard.view"}, region_id=5),
            ))
        assert exc.value.status_code == 403

    def test_area_manager_in_area_passes(self):
        db = _DBStub(
            worklog=_worklog(),
            project=_project(area_id=12),
        )
        result = asyncio.run(get_worklog_detail(
            worklog_id=42, db=db,
            current_user=_user("AREA_MANAGER",
                               perms={"dashboard.view"}, area_id=12),
        ))
        assert result["id"] == 42

    def test_area_manager_out_of_area_403(self):
        db = _DBStub(
            worklog=_worklog(),
            project=_project(area_id=99),
        )
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_worklog_detail(
                worklog_id=42, db=db,
                current_user=_user("AREA_MANAGER",
                                   perms={"dashboard.view"}, area_id=12),
            ))
        assert exc.value.status_code == 403

    def test_work_manager_assigned_passes(self):
        assignment = MagicMock(user_id=7, project_id=10, is_active=True)
        db = _DBStub(
            worklog=_worklog(project_id=10),
            assignment=assignment,
        )
        result = asyncio.run(get_worklog_detail(
            worklog_id=42, db=db,
            current_user=_user("WORK_MANAGER",
                               perms={"dashboard.view"}, user_id=7),
        ))
        assert result["id"] == 42

    def test_work_manager_unassigned_direct_url_403(self):
        """The flagship D1 regression test: WORK_MGR with a
        dashboard.view perm tries to open a financial detail page
        for a worklog on a project they're NOT assigned to."""
        db = _DBStub(
            worklog=_worklog(project_id=99),
            assignment=None,
        )
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_worklog_detail(
                worklog_id=99, db=db,
                current_user=_user("WORK_MANAGER",
                                   perms={"dashboard.view"}, user_id=7),
            ))
        assert exc.value.status_code == 403

    def test_field_worker_blocked_via_strategy(self):
        """FIELD_WORKER is in OWN_ONLY_ROLES — they can only see
        their own worklog. Trying to open another user's detail
        gets 403 from the strategy."""
        db = _DBStub(worklog=_worklog(user_id=999))
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_worklog_detail(
                worklog_id=42, db=db,
                current_user=_user("FIELD_WORKER",
                                   perms={"dashboard.view"}, user_id=42),
            ))
        assert exc.value.status_code == 403

    def test_field_worker_own_passes(self):
        db = _DBStub(worklog=_worklog(user_id=42))
        result = asyncio.run(get_worklog_detail(
            worklog_id=42, db=db,
            current_user=_user("FIELD_WORKER",
                               perms={"dashboard.view"}, user_id=42),
        ))
        assert result["id"] == 42

    def test_missing_worklog_404(self):
        """ID doesn't exist → 404 (NOT 403). Caller-friendly."""
        db = _DBStub(worklog=None)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_worklog_detail(
                worklog_id=999, db=db, current_user=_user("ADMIN"),
            ))
        assert exc.value.status_code == 404
