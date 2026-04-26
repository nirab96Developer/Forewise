"""
Phase 3 Wave 3.1.6.a — router-level tests for worklog read endpoints.

Closes Leak A (list-vs-detail mismatch) and Leak C (PDF info
disclosure) from PHASE3_WAVE316_RECON.md.

Endpoints tested:
  - GET /worklogs/{id}                  (detail; auth gate)
  - GET /worklogs/{id}/pdf              (PDF; same scope as detail)

The list / by-work-order / pending-approval endpoints have inline
service post-filtering tested at the strategy level
(test_worklog_scope_strategy.py); their router code paths are
exercised end-to-end by the existing test_worklogs_crud.py suite
running against a live DB and would have failed compile if
permission/scope wiring were broken — we verify that's still the
case in the CI subset run.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.worklogs import (
    get_worklog,
    get_worklog_pdf,
)
from app.routers import worklogs as wl_router


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


def _worklog(*, wl_id=42, project_id=10, user_id=1):
    w = MagicMock()
    w.id = wl_id
    w.project_id = project_id
    w.user_id = user_id
    w.work_order_id = None
    w.status = "DRAFT"
    w.report_number = wl_id
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
        cursor.scalar_one_or_none.return_value = self._worklog
        return cursor

    def subquery(self):
        return self


# ===========================================================================
# GET /worklogs/{id} (detail)
# ===========================================================================

class TestGetWorklogDetailScope:

    def test_admin_passes(self):
        db = _DBStub(worklog=_worklog())
        result = get_worklog(42, db, _user("ADMIN"))
        assert result is db._worklog

    def test_coordinator_passes(self):
        db = _DBStub(worklog=_worklog())
        result = get_worklog(
            42, db, _user("ORDER_COORDINATOR", perms={"worklogs.read"}),
        )
        assert result is db._worklog

    def test_accountant_passes(self):
        db = _DBStub(worklog=_worklog())
        result = get_worklog(
            42, db, _user("ACCOUNTANT", perms={"worklogs.read"}),
        )
        assert result is db._worklog

    def test_region_manager_in_region_passes(self):
        db = _DBStub(worklog=_worklog(), project=_project(region_id=5))
        result = get_worklog(
            42, db,
            _user("REGION_MANAGER", perms={"worklogs.read"}, region_id=5),
        )
        assert result is db._worklog

    def test_region_manager_out_of_region_403(self):
        db = _DBStub(worklog=_worklog(), project=_project(region_id=99))
        with pytest.raises(HTTPException) as exc:
            get_worklog(
                42, db,
                _user("REGION_MANAGER", perms={"worklogs.read"}, region_id=5),
            )
        assert exc.value.status_code == 403

    def test_area_manager_in_area_passes(self):
        db = _DBStub(worklog=_worklog(), project=_project(area_id=12))
        result = get_worklog(
            42, db,
            _user("AREA_MANAGER", perms={"worklogs.read"}, area_id=12),
        )
        assert result is db._worklog

    def test_area_manager_out_of_area_403(self):
        db = _DBStub(worklog=_worklog(), project=_project(area_id=99))
        with pytest.raises(HTTPException) as exc:
            get_worklog(
                42, db,
                _user("AREA_MANAGER", perms={"worklogs.read"}, area_id=12),
            )
        assert exc.value.status_code == 403

    def test_work_manager_assigned_passes(self):
        assignment = MagicMock(user_id=7, project_id=10, is_active=True)
        db = _DBStub(worklog=_worklog(project_id=10), assignment=assignment)
        result = get_worklog(
            42, db,
            _user("WORK_MANAGER", perms={"worklogs.read"}, user_id=7),
        )
        assert result is db._worklog

    def test_work_manager_unassigned_direct_url_403(self):
        """Flagship leak-closure: WORK_MANAGER opening /worklogs/X
        for a project they're NOT assigned to."""
        db = _DBStub(worklog=_worklog(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            get_worklog(
                99, db,
                _user("WORK_MANAGER", perms={"worklogs.read"}, user_id=7),
            )
        assert exc.value.status_code == 403

    def test_supplier_own_passes(self):
        db = _DBStub(worklog=_worklog(user_id=42))
        result = get_worklog(
            42, db,
            _user("SUPPLIER", perms={"worklogs.read", "worklogs.read_own"}, user_id=42),
        )
        assert result is db._worklog

    def test_supplier_other_user_403(self):
        db = _DBStub(worklog=_worklog(user_id=999))
        with pytest.raises(HTTPException) as exc:
            get_worklog(
                42, db,
                _user("SUPPLIER", perms={"worklogs.read", "worklogs.read_own"}, user_id=42),
            )
        assert exc.value.status_code == 403

    def test_field_worker_own_passes(self):
        db = _DBStub(worklog=_worklog(user_id=42))
        result = get_worklog(
            42, db,
            _user("FIELD_WORKER", perms={"worklogs.read"}, user_id=42),
        )
        assert result is db._worklog

    def test_field_worker_other_user_403(self):
        db = _DBStub(worklog=_worklog(user_id=999))
        with pytest.raises(HTTPException) as exc:
            get_worklog(
                42, db,
                _user("FIELD_WORKER", perms={"worklogs.read"}, user_id=42),
            )
        assert exc.value.status_code == 403

    def test_missing_worklog_404(self):
        db = _DBStub(worklog=None)
        with pytest.raises(HTTPException) as exc:
            get_worklog(999, db, _user("ADMIN"))
        assert exc.value.status_code == 404


# ===========================================================================
# GET /worklogs/{id}/pdf — same scope as detail
# ===========================================================================

class TestGetWorklogPdfScope:

    @pytest.fixture(autouse=True)
    def _stub_pdf(self, monkeypatch, tmp_path):
        """Replace the PDF generator so we don't need WeasyPrint or
        a real worklog row. Returns a path to a stub file written in
        a tmp dir."""
        import app.services.pdf_report_service as pdf_module

        stub_pdf = tmp_path / "stub.pdf"
        stub_pdf.write_bytes(b"%PDF-1.4 stub")

        monkeypatch.setattr(
            pdf_module,
            "generate_and_save_worklog_pdf",
            lambda wl_id, db: str(stub_pdf),
        )
        return None

    def test_admin_passes(self):
        db = _DBStub(worklog=_worklog())
        resp = get_worklog_pdf(42, db, _user("ADMIN"))
        assert resp.media_type == "application/pdf"
        assert resp.body == b"%PDF-1.4 stub"

    def test_supplier_own_passes(self):
        db = _DBStub(worklog=_worklog(user_id=42))
        resp = get_worklog_pdf(
            42, db,
            _user("SUPPLIER", perms={"worklogs.read"}, user_id=42),
        )
        assert resp.media_type == "application/pdf"

    def test_supplier_other_user_403(self):
        """Flagship leak-closure for Leak C: SUPPLIER cannot pull a
        PDF for a worklog they don't own. PDF exposes financial
        fields so this matters."""
        db = _DBStub(worklog=_worklog(user_id=999))
        with pytest.raises(HTTPException) as exc:
            get_worklog_pdf(
                42, db,
                _user("SUPPLIER", perms={"worklogs.read"}, user_id=42),
            )
        assert exc.value.status_code == 403

    def test_region_manager_in_region_passes(self):
        db = _DBStub(worklog=_worklog(), project=_project(region_id=5))
        resp = get_worklog_pdf(
            42, db,
            _user("REGION_MANAGER", perms={"worklogs.read"}, region_id=5),
        )
        assert resp.media_type == "application/pdf"

    def test_region_manager_out_of_region_403(self):
        db = _DBStub(worklog=_worklog(), project=_project(region_id=99))
        with pytest.raises(HTTPException) as exc:
            get_worklog_pdf(
                42, db,
                _user("REGION_MANAGER", perms={"worklogs.read"}, region_id=5),
            )
        assert exc.value.status_code == 403

    def test_work_manager_unassigned_403(self):
        db = _DBStub(worklog=_worklog(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            get_worklog_pdf(
                99, db,
                _user("WORK_MANAGER", perms={"worklogs.read"}, user_id=7),
            )
        assert exc.value.status_code == 403

    def test_missing_worklog_404(self):
        db = _DBStub(worklog=None)
        with pytest.raises(HTTPException) as exc:
            get_worklog_pdf(999, db, _user("ADMIN"))
        assert exc.value.status_code == 404
