"""
Phase 3 Wave 2.1.a — scope enforcement on /activity-logs/{id} detail.
Phase 3 Wave 2.1.b — verification that the worklog endpoints actually
emit the right activity log events (via the service layer that
already calls activity_logger.log_worklog_*).

Wave 2.1.a — G4 closure
-----------------------
Before this wave, GET /activity-logs/{log_id} returned any row to
any authenticated caller. The list endpoint was correctly scoped
(my / area / region / system); the detail wasn't. Now both share
a per-row predicate so a user who can't see a log in their list
gets a clean 403 on direct URL access.

Wave 2.1.b — audit-trail verification
-------------------------------------
The original recon flagged G1 as "worklogs.py never calls
log_worklog_*". A second look found the helpers ARE called — at
the service layer (worklog_service.py:395, 580, 627, 708). The
gap was test coverage, not wiring. These tests pin the contract
so a future refactor of WorklogService can't silently drop the
audit trail.
"""
import inspect
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.routers.activity_logs import (
    _user_can_see_log,
    _get_scope_for_role,
    get_activity_log,
)
from app.services.worklog_service import WorklogService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(role_code, *, user_id=1, region_id=None, area_id=None):
    user = MagicMock()
    user.id = user_id
    user.role_id = 1
    user.is_active = True
    user.region_id = region_id
    user.area_id = area_id
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = []
    user._permissions = set()
    return user


def _log(*, log_id=1, user_id=2, category=None):
    log = MagicMock()
    log.id = log_id
    log.user_id = user_id
    log.category = category
    log.activity_type = "work_order"
    log.action = "work_order.created"
    log.entity_type = "work_order"
    log.entity_id = 100
    log.created_at = None
    return log


class _DBStub:
    """Minimal session for the detail handler.

    Returns a seeded log for the first .first() call, and a seeded
    user (the log's owner, for region/area scope checks) for the
    second .first() call when looking up `User`.
    """

    def __init__(self, *, log=None, log_owner=None):
        self._log = log
        self._log_owner = log_owner
        self._current_model = None

    def query(self, *args):
        first = args[0] if args else None
        self._current_model = getattr(first, "__name__", str(first))
        return self

    def filter(self, *a, **kw):
        return self

    def first(self):
        if self._current_model == "ActivityLog":
            return self._log
        if self._current_model == "User":
            return self._log_owner
        return None

    def all(self):
        return []


# ===========================================================================
# 2.1.a — _user_can_see_log predicate
# ===========================================================================

class TestScopePredicateGlobal:

    def test_admin_sees_anyones_log(self):
        assert _user_can_see_log(
            _DBStub(),
            _user("ADMIN", user_id=1),
            _log(user_id=999),
        )

    def test_super_admin_sees_anyones_log(self):
        assert _user_can_see_log(
            _DBStub(),
            _user("SUPER_ADMIN", user_id=1),
            _log(user_id=999),
        )

    def test_admin_sees_null_user_id_logs(self):
        """System events with user_id=None (e.g. supplier timer
        expiry) — admin should see them."""
        assert _user_can_see_log(
            _DBStub(),
            _user("ADMIN"),
            _log(user_id=None),
        )


class TestScopePredicateOwnLog:
    """Owner always passes regardless of role / scope."""

    def test_supplier_sees_own_log(self):
        assert _user_can_see_log(
            _DBStub(),
            _user("SUPPLIER", user_id=42),
            _log(user_id=42),
        )

    def test_field_worker_sees_own_log(self):
        assert _user_can_see_log(
            _DBStub(),
            _user("FIELD_WORKER", user_id=42),
            _log(user_id=42),
        )

    def test_work_manager_sees_own_log(self):
        assert _user_can_see_log(
            _DBStub(),
            _user("WORK_MANAGER", user_id=42),
            _log(user_id=42, category="operational"),
        )


class TestScopePredicateOtherUser:
    """Non-admin / non-owner — denied."""

    def test_supplier_blocked_from_other_user_log(self):
        assert not _user_can_see_log(
            _DBStub(),
            _user("SUPPLIER", user_id=42),
            _log(user_id=999),
        )

    def test_field_worker_blocked_from_other_user_log(self):
        assert not _user_can_see_log(
            _DBStub(),
            _user("FIELD_WORKER", user_id=42),
            _log(user_id=999),
        )

    def test_work_manager_blocked_from_other_user_log(self):
        assert not _user_can_see_log(
            _DBStub(),
            _user("WORK_MANAGER", user_id=42),
            _log(user_id=999, category="operational"),
        )


class TestScopePredicateRegion:

    def test_region_manager_sees_log_from_same_region(self):
        log_owner = _user("WORK_MANAGER", user_id=99, region_id=5)
        db = _DBStub(log_owner=log_owner)
        assert _user_can_see_log(
            db,
            _user("REGION_MANAGER", user_id=42, region_id=5),
            _log(user_id=99),
        )

    def test_region_manager_blocked_from_other_region(self):
        log_owner = _user("WORK_MANAGER", user_id=99, region_id=99)
        db = _DBStub(log_owner=log_owner)
        assert not _user_can_see_log(
            db,
            _user("REGION_MANAGER", user_id=42, region_id=5),
            _log(user_id=99),
        )

    def test_region_manager_without_region_id_only_sees_own(self):
        db = _DBStub()
        assert not _user_can_see_log(
            db,
            _user("REGION_MANAGER", user_id=42, region_id=None),
            _log(user_id=99),
        )


class TestScopePredicateArea:

    def test_area_manager_sees_log_from_same_area(self):
        log_owner = _user("WORK_MANAGER", user_id=99, area_id=12)
        db = _DBStub(log_owner=log_owner)
        assert _user_can_see_log(
            db,
            _user("AREA_MANAGER", user_id=42, area_id=12),
            _log(user_id=99),
        )

    def test_area_manager_blocked_from_other_area(self):
        log_owner = _user("WORK_MANAGER", user_id=99, area_id=99)
        db = _DBStub(log_owner=log_owner)
        assert not _user_can_see_log(
            db,
            _user("AREA_MANAGER", user_id=42, area_id=12),
            _log(user_id=99),
        )


class TestScopePredicateCategoryAutoFilter:
    """Mirrors the list endpoint's role × category auto-filter."""

    def test_accountant_sees_financial(self):
        assert _user_can_see_log(
            _DBStub(),
            _user("ACCOUNTANT", user_id=42),
            _log(user_id=42, category="financial"),
        )

    def test_accountant_blocked_from_operational(self):
        """ACCOUNTANT viewing an operational log they happen to own
        is still blocked by the category auto-filter — matches the
        list behavior."""
        assert not _user_can_see_log(
            _DBStub(),
            _user("ACCOUNTANT", user_id=42),
            _log(user_id=42, category="operational"),
        )

    def test_work_manager_sees_operational(self):
        assert _user_can_see_log(
            _DBStub(),
            _user("WORK_MANAGER", user_id=42),
            _log(user_id=42, category="operational"),
        )

    def test_work_manager_blocked_from_financial(self):
        assert not _user_can_see_log(
            _DBStub(),
            _user("WORK_MANAGER", user_id=42),
            _log(user_id=42, category="financial"),
        )

    def test_coordinator_sees_operational(self):
        assert _user_can_see_log(
            _DBStub(),
            _user("ORDER_COORDINATOR", user_id=42),
            _log(user_id=42, category="operational"),
        )

    def test_coordinator_blocked_from_financial(self):
        assert not _user_can_see_log(
            _DBStub(),
            _user("ORDER_COORDINATOR", user_id=42),
            _log(user_id=42, category="financial"),
        )


# ===========================================================================
# 2.1.a — get_activity_log endpoint integration
# ===========================================================================

class TestGetActivityLogEndpoint:

    def test_admin_can_open_anyones_log(self):
        import asyncio
        db = _DBStub(log=_log(user_id=999, category="operational"))
        result = asyncio.run(get_activity_log(
            log_id=1, db=db, current_user=_user("ADMIN", user_id=1),
        ))
        assert result is db._log

    def test_owner_can_open_own_log(self):
        import asyncio
        db = _DBStub(log=_log(user_id=42))
        result = asyncio.run(get_activity_log(
            log_id=1, db=db,
            current_user=_user("WORK_MANAGER", user_id=42),
        ))
        assert result is db._log

    def test_non_owner_non_admin_403(self):
        """The G4 leak-closure regression test: a non-owner non-admin
        user MUST get 403 on direct URL access to a log they can't
        see in their list."""
        import asyncio
        db = _DBStub(log=_log(user_id=999))
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_activity_log(
                log_id=1, db=db,
                current_user=_user("WORK_MANAGER", user_id=42),
            ))
        assert exc.value.status_code == 403

    def test_supplier_blocked_from_other_user_log(self):
        import asyncio
        db = _DBStub(log=_log(user_id=999))
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_activity_log(
                log_id=1, db=db,
                current_user=_user("SUPPLIER", user_id=42),
            ))
        assert exc.value.status_code == 403

    def test_accountant_blocked_from_operational_log(self):
        """Even owner-on-paper, the category auto-filter catches it."""
        import asyncio
        db = _DBStub(log=_log(user_id=42, category="operational"))
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_activity_log(
                log_id=1, db=db,
                current_user=_user("ACCOUNTANT", user_id=42),
            ))
        assert exc.value.status_code == 403

    def test_region_manager_in_scope_passes(self):
        import asyncio
        db = _DBStub(
            log=_log(user_id=99),
            log_owner=_user("WORK_MANAGER", user_id=99, region_id=5),
        )
        result = asyncio.run(get_activity_log(
            log_id=1, db=db,
            current_user=_user("REGION_MANAGER", user_id=42, region_id=5),
        ))
        assert result is db._log

    def test_region_manager_out_of_scope_403(self):
        import asyncio
        db = _DBStub(
            log=_log(user_id=99),
            log_owner=_user("WORK_MANAGER", user_id=99, region_id=99),
        )
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_activity_log(
                log_id=1, db=db,
                current_user=_user("REGION_MANAGER", user_id=42, region_id=5),
            ))
        assert exc.value.status_code == 403

    def test_missing_log_404(self):
        import asyncio
        db = _DBStub(log=None)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_activity_log(
                log_id=999, db=db, current_user=_user("ADMIN"),
            ))
        assert exc.value.status_code == 404


class TestGetScopeForRole:
    """Pin the role → max-scope mapping."""

    def test_admin_system(self):
        assert _get_scope_for_role("ADMIN") == "system"

    def test_super_admin_system(self):
        assert _get_scope_for_role("SUPER_ADMIN") == "system"

    def test_region_manager_region(self):
        assert _get_scope_for_role("REGION_MANAGER") == "region"

    def test_area_manager_area(self):
        assert _get_scope_for_role("AREA_MANAGER") == "area"

    def test_other_roles_default_to_my(self):
        for role in ("WORK_MANAGER", "ORDER_COORDINATOR", "ACCOUNTANT",
                     "SUPPLIER", "FIELD_WORKER", "MYSTERY"):
            assert _get_scope_for_role(role) == "my"


# ===========================================================================
# 2.1.b — verify worklog audit trail is wired
# ===========================================================================

class TestWorklogAuditWired:
    """The recon's G1 was a false alarm — worklog_service.py DOES call
    activity_logger.log_worklog_* internally. These regression-pin
    tests ensure the calls aren't silently removed in a future
    refactor of the service layer.
    """

    def test_create_calls_log_worklog_created(self):
        src = inspect.getsource(WorklogService.create)
        assert "log_worklog_created" in src, (
            "WorklogService.create lost its activity_logger.log_worklog_created "
            "call — audit trail broken. See PHASE3_WAVE2_RECON.md G1."
        )

    def test_submit_calls_log_worklog_submitted(self):
        src = inspect.getsource(WorklogService.submit)
        assert "log_worklog_submitted" in src

    def test_approve_calls_log_worklog_approved(self):
        src = inspect.getsource(WorklogService.approve)
        assert "log_worklog_approved" in src

    def test_reject_calls_log_worklog_rejected(self):
        src = inspect.getsource(WorklogService.reject)
        assert "log_worklog_rejected" in src


class TestWorklogAuditHelpers:
    """Verify the helpers themselves still build the expected
    ActivityLog payload. Catches accidental schema drift."""

    def _captured_log(self, fn, **kwargs):
        """Run a logger helper with mocked DB + mocked
        ActivityLogService and return the args it received."""
        from app.services import activity_logger as _al

        captured = {}

        class FakeService:
            def log_activity(self, **kw):
                captured.update(kw)

        with patch.object(_al, "_activity_log_service", FakeService()):
            fn(db=MagicMock(), **kwargs)

        return captured

    def test_log_worklog_created_carries_entity(self):
        from app.services.activity_logger import log_worklog_created

        captured = self._captured_log(
            log_worklog_created,
            worklog_id=42, user_id=7,
            work_order_id=10, project_id=5,
            is_standard=True, total_hours=9.0,
        )
        assert captured["activity_type"] == "worklog"
        assert captured["action"] == "worklog.created"
        assert captured["entity_type"] == "worklog"
        assert captured["entity_id"] == 42
        assert captured["user_id"] == 7

    def test_log_worklog_submitted_carries_entity(self):
        from app.services.activity_logger import log_worklog_submitted

        captured = self._captured_log(
            log_worklog_submitted,
            worklog_id=42, user_id=7,
            work_order_id=10, project_id=5,
        )
        assert captured["action"] == "worklog.submitted"
        assert captured["entity_id"] == 42

    def test_log_worklog_approved_carries_approver(self):
        from app.services.activity_logger import log_worklog_approved

        captured = self._captured_log(
            log_worklog_approved,
            worklog_id=42, user_id=7, approved_by_id=11,
        )
        assert captured["action"] == "worklog.approved"
        assert captured["details"]["approved_by_id"] == 11

    def test_log_worklog_rejected_carries_reason(self):
        from app.services.activity_logger import log_worklog_rejected

        captured = self._captured_log(
            log_worklog_rejected,
            worklog_id=42, user_id=7, rejected_by_id=11,
            reason="incomplete data",
        )
        assert captured["action"] == "worklog.rejected"
        assert captured["details"]["rejected_by_id"] == 11
        assert captured["details"]["reason"] == "incomplete data"
