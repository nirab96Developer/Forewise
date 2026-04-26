"""
Phase 3 Wave 3.1.6.d — pre-create scope check on worklog create
endpoints.

Closes the gap where any role with `worklogs.create` could log
hours against any WO / project. The migration adds a single helper
(`_check_create_scope`) called from all four create endpoints:

  POST /worklogs           → WorkOrderScopeStrategy or
                             ProjectScopeStrategy depending on
                             which payload field is set.
  POST /worklogs/standard  → WorkOrderScopeStrategy (WO from query).
  POST /worklogs/manual    → WorkOrderScopeStrategy.
  POST /worklogs/storage   → WorkOrderScopeStrategy.

Today only ADMIN holds `worklogs.create` (via require_permission
bypass), so the strategy is a no-op for the only caller in
production. The migration is meaningful the day the perm is
granted to AREA / REGION / WORK_MANAGER — at which point the
strategy enforces scope automatically.
"""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.worklogs import (
    _check_create_scope,
    create_worklog,
    create_standard_worklog,
    create_manual_worklog,
    create_storage_worklog,
)
from app.routers import worklogs as wl_router
from app.schemas.worklog import WorklogCreate


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


def _wo(*, wo_id=10, project_id=10, deleted=False):
    w = MagicMock()
    w.id = wo_id
    w.project_id = project_id
    w.deleted_at = None if not deleted else MagicMock()
    w.status = "APPROVED_AND_SENT"
    return w


def _project(*, project_id=10, region_id=None, area_id=None):
    p = MagicMock()
    p.id = project_id
    p.region_id = region_id
    p.area_id = area_id
    return p


class _DBStub:
    def __init__(self, *, work_order=None, project=None, assignment=None):
        self._work_order = work_order
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
            return self._work_order
        if self._current_model == "Project":
            return self._project
        if self._current_model == "ProjectAssignment":
            return self._assignment
        return None

    def all(self):
        return []

    def subquery(self):
        return self


@pytest.fixture(autouse=True)
def _mock_service(monkeypatch):
    fake = MagicMock()
    fake.create.return_value = MagicMock(id=99, project_id=10)
    monkeypatch.setattr(wl_router, "worklog_service", fake)
    monkeypatch.setattr(wl_router, "notify_worklog_created", lambda *a, **k: None)
    monkeypatch.setattr(wl_router, "_send_worklog_stage1_emails", lambda *a, **k: None)
    return fake


# ===========================================================================
# 1. _check_create_scope helper — direct unit tests
# ===========================================================================

class TestCheckCreateScopeWithWorkOrder:

    def test_admin_passes(self):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(region_id=99, area_id=99))
        _check_create_scope(db, _user("ADMIN"), work_order_id=10)

    def test_coordinator_passes(self):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(region_id=99, area_id=99))
        _check_create_scope(
            db,
            _user("ORDER_COORDINATOR", perms={"worklogs.create"}),
            work_order_id=10,
        )

    def test_area_manager_in_area_passes(self):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(area_id=12))
        _check_create_scope(
            db,
            _user("AREA_MANAGER", perms={"worklogs.create"}, area_id=12),
            work_order_id=10,
        )

    def test_area_manager_out_of_area_403(self):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(area_id=99))
        with pytest.raises(HTTPException) as exc:
            _check_create_scope(
                db,
                _user("AREA_MANAGER", perms={"worklogs.create"}, area_id=12),
                work_order_id=10,
            )
        assert exc.value.status_code == 403

    def test_region_manager_in_region_passes(self):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(region_id=5))
        _check_create_scope(
            db,
            _user("REGION_MANAGER", perms={"worklogs.create"}, region_id=5),
            work_order_id=10,
        )

    def test_region_manager_out_of_region_403(self):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(region_id=99))
        with pytest.raises(HTTPException) as exc:
            _check_create_scope(
                db,
                _user("REGION_MANAGER", perms={"worklogs.create"}, region_id=5),
                work_order_id=10,
            )
        assert exc.value.status_code == 403

    def test_work_manager_assigned_passes(self):
        assignment = MagicMock(user_id=7, project_id=10, is_active=True)
        db = _DBStub(work_order=_wo(project_id=10), assignment=assignment)
        _check_create_scope(
            db,
            _user("WORK_MANAGER", perms={"worklogs.create"}, user_id=7),
            work_order_id=10,
        )

    def test_work_manager_unassigned_403(self):
        db = _DBStub(work_order=_wo(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            _check_create_scope(
                db,
                _user("WORK_MANAGER", perms={"worklogs.create"}, user_id=7),
                work_order_id=10,
            )
        assert exc.value.status_code == 403

    def test_supplier_blocked_by_workorder_strategy(self):
        """SUPPLIER is in WorkOrderScopeStrategy's blocked list — they
        belong on /supplier-portal, never on /worklogs creating
        directly. Even if granted worklogs.create by mistake, the
        strategy denies."""
        db = _DBStub(work_order=_wo())
        with pytest.raises(HTTPException) as exc:
            _check_create_scope(
                db,
                _user("SUPPLIER", perms={"worklogs.create"}),
                work_order_id=10,
            )
        assert exc.value.status_code == 403

    def test_missing_work_order_404(self):
        db = _DBStub(work_order=None)
        with pytest.raises(HTTPException) as exc:
            _check_create_scope(db, _user("ADMIN"), work_order_id=999)
        assert exc.value.status_code == 404


class TestCheckCreateScopeWithProjectId:
    """When work_order_id is None but project_id is set, fall back
    to ProjectScopeStrategy."""

    def test_admin_passes(self):
        db = _DBStub(project=_project(region_id=99, area_id=99))
        _check_create_scope(db, _user("ADMIN"), project_id=10)

    def test_area_manager_in_area_passes(self):
        db = _DBStub(project=_project(area_id=12))
        _check_create_scope(
            db,
            _user("AREA_MANAGER", perms={"worklogs.create"}, area_id=12),
            project_id=10,
        )

    def test_area_manager_out_of_area_403(self):
        db = _DBStub(project=_project(area_id=99))
        with pytest.raises(HTTPException) as exc:
            _check_create_scope(
                db,
                _user("AREA_MANAGER", perms={"worklogs.create"}, area_id=12),
                project_id=10,
            )
        assert exc.value.status_code == 403

    def test_work_manager_unassigned_403(self):
        db = _DBStub(project=_project(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            _check_create_scope(
                db,
                _user("WORK_MANAGER", perms={"worklogs.create"}, user_id=7),
                project_id=99,
            )
        assert exc.value.status_code == 403

    def test_missing_project_404(self):
        db = _DBStub(project=None)
        with pytest.raises(HTTPException) as exc:
            _check_create_scope(db, _user("ADMIN"), project_id=999)
        assert exc.value.status_code == 404


class TestCheckCreateScopeRootless:
    """Both work_order_id and project_id are None → no scope check
    runs. Preserves the legacy 'rootless worklog' path; admin-only
    gates stay via the existing perm."""

    def test_no_args_no_scope_check(self):
        db = _DBStub()
        _check_create_scope(db, _user("ADMIN"))


# ===========================================================================
# 2. create_worklog endpoint
# ===========================================================================

def _payload(work_order_id=None, project_id=None):
    p = WorklogCreate(
        work_order_id=work_order_id,
        project_id=project_id,
        report_date=date(2026, 4, 26),
        report_type="standard",
        work_hours=Decimal("9.0"),
        break_hours=Decimal("1.5"),
        total_hours=Decimal("9"),
        is_standard=True,
    )
    return p


class TestCreateWorklog:

    def test_admin_with_wo_passes(self, _mock_service):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(region_id=99, area_id=99))
        create_worklog(_payload(work_order_id=10), db, _user("ADMIN"))
        _mock_service.create.assert_called_once()

    def test_area_manager_in_area_with_wo_passes(self, _mock_service):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(area_id=12))
        create_worklog(
            _payload(work_order_id=10),
            db,
            _user("AREA_MANAGER", perms={"worklogs.create"}, area_id=12),
        )
        _mock_service.create.assert_called_once()

    def test_area_manager_out_of_area_with_wo_403(self, _mock_service):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(area_id=99))
        with pytest.raises(HTTPException) as exc:
            create_worklog(
                _payload(work_order_id=10),
                db,
                _user("AREA_MANAGER", perms={"worklogs.create"}, area_id=12),
            )
        assert exc.value.status_code == 403
        _mock_service.create.assert_not_called()

    def test_region_manager_in_region_passes(self, _mock_service):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(region_id=5))
        create_worklog(
            _payload(work_order_id=10),
            db,
            _user("REGION_MANAGER", perms={"worklogs.create"}, region_id=5),
        )
        _mock_service.create.assert_called_once()

    def test_region_manager_out_of_region_403(self, _mock_service):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(region_id=99))
        with pytest.raises(HTTPException) as exc:
            create_worklog(
                _payload(work_order_id=10),
                db,
                _user("REGION_MANAGER", perms={"worklogs.create"}, region_id=5),
            )
        assert exc.value.status_code == 403

    def test_work_manager_assigned_passes(self, _mock_service):
        assignment = MagicMock(user_id=7, project_id=10, is_active=True)
        db = _DBStub(work_order=_wo(project_id=10), assignment=assignment)
        create_worklog(
            _payload(work_order_id=10),
            db,
            _user("WORK_MANAGER", perms={"worklogs.create"}, user_id=7),
        )
        _mock_service.create.assert_called_once()

    def test_work_manager_unassigned_direct_url_403(self, _mock_service):
        """Flagship leak-closure: WORK_MGR with worklogs.create can
        NOT create on a project they're not assigned to."""
        db = _DBStub(work_order=_wo(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            create_worklog(
                _payload(work_order_id=10),
                db,
                _user("WORK_MANAGER", perms={"worklogs.create"}, user_id=7),
            )
        assert exc.value.status_code == 403

    def test_supplier_blocked_by_perm_403(self, _mock_service):
        """SUPPLIER doesn't have worklogs.create in DB. They're
        blocked at the perm gate before reaching scope."""
        db = _DBStub(work_order=_wo(project_id=10))
        with pytest.raises(HTTPException) as exc:
            create_worklog(
                _payload(work_order_id=10),
                db,
                _user("SUPPLIER", perms={"worklogs.read_own", "worklogs.submit"}),
            )
        assert exc.value.status_code == 403

    def test_supplier_with_create_perm_blocked_by_strategy(self, _mock_service):
        """Belt-and-braces: even if SUPPLIER got worklogs.create by
        mistake, WorkOrderScopeStrategy still denies them — they
        belong on the supplier portal flow, not /worklogs."""
        db = _DBStub(work_order=_wo(project_id=10))
        with pytest.raises(HTTPException) as exc:
            create_worklog(
                _payload(work_order_id=10),
                db,
                _user("SUPPLIER", perms={"worklogs.create"}),
            )
        assert exc.value.status_code == 403

    def test_with_project_id_only_uses_project_strategy(self, _mock_service):
        """No work_order_id but project_id set → ProjectScopeStrategy
        decides. AREA_MGR in area passes."""
        db = _DBStub(project=_project(area_id=12))
        create_worklog(
            _payload(project_id=10),
            db,
            _user("AREA_MANAGER", perms={"worklogs.create"}, area_id=12),
        )
        _mock_service.create.assert_called_once()

    def test_with_project_id_out_of_scope_403(self, _mock_service):
        db = _DBStub(project=_project(area_id=99))
        with pytest.raises(HTTPException) as exc:
            create_worklog(
                _payload(project_id=10),
                db,
                _user("AREA_MANAGER", perms={"worklogs.create"}, area_id=12),
            )
        assert exc.value.status_code == 403

    def test_rootless_worklog_admin_passes(self, _mock_service):
        """No work_order_id, no project_id → no scope check (legacy
        path). Admin succeeds via RBAC alone."""
        db = _DBStub()
        create_worklog(_payload(), db, _user("ADMIN"))
        _mock_service.create.assert_called_once()

    def test_missing_work_order_404(self, _mock_service):
        db = _DBStub(work_order=None)
        with pytest.raises(HTTPException) as exc:
            create_worklog(_payload(work_order_id=999), db, _user("ADMIN"))
        assert exc.value.status_code == 404
        _mock_service.create.assert_not_called()


# ===========================================================================
# 3. create_standard / create_manual / create_storage
# ===========================================================================

class TestCreateStandardWorklog:

    def test_admin_passes(self, _mock_service):
        db = _DBStub(work_order=_wo(project_id=10))
        create_standard_worklog(
            work_order_id=10, report_date="2026-04-26",
            notes=None, db=db, current_user=_user("ADMIN"),
        )
        _mock_service.create.assert_called_once()

    def test_area_manager_out_of_area_403(self, _mock_service):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(area_id=99))
        with pytest.raises(HTTPException) as exc:
            create_standard_worklog(
                work_order_id=10, report_date="2026-04-26",
                notes=None, db=db,
                current_user=_user("AREA_MANAGER", perms={"worklogs.create"}, area_id=12),
            )
        assert exc.value.status_code == 403

    def test_work_manager_unassigned_403(self, _mock_service):
        db = _DBStub(work_order=_wo(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            create_standard_worklog(
                work_order_id=99, report_date="2026-04-26",
                notes=None, db=db,
                current_user=_user("WORK_MANAGER", perms={"worklogs.create"}, user_id=7),
            )
        assert exc.value.status_code == 403

    def test_missing_work_order_404(self, _mock_service):
        db = _DBStub(work_order=None)
        with pytest.raises(HTTPException) as exc:
            create_standard_worklog(
                work_order_id=999, report_date="2026-04-26",
                notes=None, db=db, current_user=_user("ADMIN"),
            )
        assert exc.value.status_code == 404


class TestCreateManualWorklog:

    def test_admin_passes(self, _mock_service):
        db = _DBStub(work_order=_wo(project_id=10))
        create_manual_worklog(
            work_order_id=10, report_date="2026-04-26",
            activity_code="1", work_hours=8.0, break_hours=1.0,
            activity_description="x", notes=None,
            db=db, current_user=_user("ADMIN"),
        )
        _mock_service.create.assert_called_once()

    def test_region_manager_out_of_region_403(self, _mock_service):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(region_id=99))
        with pytest.raises(HTTPException) as exc:
            create_manual_worklog(
                work_order_id=10, report_date="2026-04-26",
                activity_code="1", work_hours=8.0, break_hours=1.0,
                activity_description="x", notes=None,
                db=db,
                current_user=_user("REGION_MANAGER", perms={"worklogs.create"}, region_id=5),
            )
        assert exc.value.status_code == 403


class TestCreateStorageWorklog:

    def test_admin_passes(self, _mock_service):
        db = _DBStub(work_order=_wo(project_id=10))
        create_storage_worklog(
            work_order_id=10, report_date="2026-04-26",
            notes=None, db=db, current_user=_user("ADMIN"),
        )
        _mock_service.create.assert_called_once()

    def test_area_manager_in_area_passes(self, _mock_service):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(area_id=12))
        create_storage_worklog(
            work_order_id=10, report_date="2026-04-26",
            notes=None, db=db,
            current_user=_user("AREA_MANAGER", perms={"worklogs.create"}, area_id=12),
        )
        _mock_service.create.assert_called_once()

    def test_area_manager_out_of_area_403(self, _mock_service):
        db = _DBStub(work_order=_wo(project_id=10),
                     project=_project(area_id=99))
        with pytest.raises(HTTPException) as exc:
            create_storage_worklog(
                work_order_id=10, report_date="2026-04-26",
                notes=None, db=db,
                current_user=_user("AREA_MANAGER", perms={"worklogs.create"}, area_id=12),
            )
        assert exc.value.status_code == 403
