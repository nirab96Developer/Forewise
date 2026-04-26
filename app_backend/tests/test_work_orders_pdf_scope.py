"""
Phase 3 Wave 1.3.d — scope enforcement on the WO PDF endpoint.

Closes the info-disclosure documented in PHASE3_WAVE13_RECON.md
(row 14): GET /work-orders/{id}/pdf was gated by `work_orders.read`
only — any user with that perm could download a PDF for any WO,
which exposes financial fields (frozen_amount, hourly_rate,
remaining_frozen, status) for projects outside their scope.

A subtle leak in the legacy code: the PDF generator raised on
permission-class errors, falling through to an HTML fallback path
that re-queried the WO and rebuilt the same content. The migration
also pulls fetch+authorize OUT of the try/except so 403/404 propagate
cleanly instead of being silently transformed into an HTML 200.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.work_orders import get_work_order_pdf
from app.routers import work_orders as wo_router
import app.services.pdf_documents as pdf_module


# ---------------------------------------------------------------------------
# Helpers (mirror the rest of Wave 1.3 tests)
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


def _wo(*, wo_id=42, project_id=10, status="APPROVED_AND_SENT"):
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


@pytest.fixture(autouse=True)
def _stub_pdf(monkeypatch):
    """Replace the PDF generator with a minimal one — its content
    isn't under test, only the auth gate is."""
    monkeypatch.setattr(pdf_module, "generate_work_order_pdf",
                        lambda wo_id, db: b"%PDF-1.4 stub")
    return None


# ===========================================================================
# Auth gate behavior
# ===========================================================================

class TestPdfScope:

    def test_admin_passes(self):
        db = _DBStub(wo=_wo())
        resp = get_work_order_pdf(42, db, _user("ADMIN"))
        assert resp.media_type == "application/pdf"
        assert resp.body == b"%PDF-1.4 stub"

    def test_coordinator_passes(self):
        db = _DBStub(wo=_wo())
        resp = get_work_order_pdf(
            42, db, _user("ORDER_COORDINATOR", perms={"work_orders.read"})
        )
        assert resp.media_type == "application/pdf"

    def test_accountant_passes(self):
        """ACCOUNTANT is in GLOBAL_ROLES (read-only by perm convention)."""
        db = _DBStub(wo=_wo())
        resp = get_work_order_pdf(
            42, db, _user("ACCOUNTANT", perms={"work_orders.read"})
        )
        assert resp.media_type == "application/pdf"

    def test_region_manager_in_scope_passes(self):
        db = _DBStub(wo=_wo(), project=_project(region_id=5))
        resp = get_work_order_pdf(
            42, db,
            _user("REGION_MANAGER", perms={"work_orders.read"}, region_id=5),
        )
        assert resp.media_type == "application/pdf"

    def test_region_manager_out_of_scope_403(self):
        db = _DBStub(wo=_wo(), project=_project(region_id=99))
        with pytest.raises(HTTPException) as exc:
            get_work_order_pdf(
                42, db,
                _user("REGION_MANAGER", perms={"work_orders.read"}, region_id=5),
            )
        assert exc.value.status_code == 403

    def test_area_manager_in_scope_passes(self):
        db = _DBStub(wo=_wo(), project=_project(area_id=12))
        resp = get_work_order_pdf(
            42, db,
            _user("AREA_MANAGER", perms={"work_orders.read"}, area_id=12),
        )
        assert resp.media_type == "application/pdf"

    def test_area_manager_out_of_scope_403(self):
        db = _DBStub(wo=_wo(), project=_project(area_id=99))
        with pytest.raises(HTTPException) as exc:
            get_work_order_pdf(
                42, db,
                _user("AREA_MANAGER", perms={"work_orders.read"}, area_id=12),
            )
        assert exc.value.status_code == 403

    def test_work_manager_assigned_passes(self):
        assignment = MagicMock(user_id=7, project_id=10, is_active=True)
        db = _DBStub(wo=_wo(project_id=10), assignment=assignment)
        resp = get_work_order_pdf(
            42, db,
            _user("WORK_MANAGER", perms={"work_orders.read"}, user_id=7),
        )
        assert resp.media_type == "application/pdf"

    def test_work_manager_unassigned_direct_url_403(self):
        """Flagship leak-closure: a WORK_MGR cannot pull a financial
        PDF for a stranger's WO via direct URL access."""
        db = _DBStub(wo=_wo(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            get_work_order_pdf(
                99, db,
                _user("WORK_MANAGER", perms={"work_orders.read"}, user_id=7),
            )
        assert exc.value.status_code == 403

    def test_supplier_403(self):
        db = _DBStub(wo=_wo())
        with pytest.raises(HTTPException) as exc:
            get_work_order_pdf(
                42, db, _user("SUPPLIER", perms={"work_orders.read"}),
            )
        assert exc.value.status_code == 403

    def test_missing_wo_404(self):
        db = _DBStub(wo=None)
        with pytest.raises(HTTPException) as exc:
            get_work_order_pdf(999, db, _user("ADMIN"))
        assert exc.value.status_code == 404

    def test_pdf_generator_failure_falls_back_to_html_for_authorized_user(
        self, monkeypatch,
    ):
        """Sanity: the legacy HTML fallback still works for authorized
        callers when WeasyPrint blows up. We don't lose graceful
        degradation when adding the scope check."""
        def boom(wo_id, db):
            raise RuntimeError("weasyprint down")

        monkeypatch.setattr(pdf_module, "generate_work_order_pdf", boom)
        # `_build_work_order_html` issues raw SQL via db.execute for
        # project/supplier/equipment lookups — out of scope here. Stub
        # it to a minimal known string.
        monkeypatch.setattr(
            wo_router,
            "_build_work_order_html",
            lambda wo, db: "<html>stub</html>",
        )

        db = _DBStub(wo=_wo())
        resp = get_work_order_pdf(42, db, _user("ADMIN"))
        # HTMLResponse — auth was OK, only PDF generation failed.
        assert resp.media_type == "text/html"

    def test_pdf_generator_failure_does_not_leak_to_unauthorized_user(
        self, monkeypatch,
    ):
        """Counter-test for the above: even if PDF generation would
        have failed and fallen back to HTML, an unauthorized caller
        gets 403 BEFORE that path runs. The legacy code re-queried
        the WO inside the except block and rendered HTML for any
        caller — that path is gone now."""
        def boom(wo_id, db):
            raise RuntimeError("weasyprint down")

        monkeypatch.setattr(pdf_module, "generate_work_order_pdf", boom)

        db = _DBStub(wo=_wo(project_id=99), assignment=None)
        with pytest.raises(HTTPException) as exc:
            get_work_order_pdf(
                99, db,
                _user("WORK_MANAGER", perms={"work_orders.read"}, user_id=7),
            )
        assert exc.value.status_code == 403
