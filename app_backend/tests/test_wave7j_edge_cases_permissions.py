"""
Tests for Wave 7.J — final Wave 7 edge cases.

Three small endpoints with different enforcement profiles:

  POST /otp/cleanup
    Was: inline `current_user.role.code == "ADMIN"` check.
    Now: require_permission("system.settings") for consistency.

  POST /work-order-coordination-logs
    Was: only `get_current_active_user` — any authenticated user could
    inject coordination notes onto any WO.
    Now: require_permission("work_orders.coordinate")
    (assigned to ADMIN, ORDER_COORDINATOR, REGION_MANAGER in DB).

  POST /sync/batch
    Stays auth-only by design. Every sub-operation forwards
    current_user.id to the underlying service, which applies its own
    permission/ownership rules. The batch wrapper itself can't escalate.
    Tests assert this contract.
"""
import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.otp import cleanup_expired_tokens
from app.routers.work_order_coordination_logs import (
    CoordinationLogCreate,
    create_coordination_log,
)
from app.routers.sync import (
    SyncBatchRequest,
    SyncOperation,
    sync_batch,
)


def _user(role_code: str, *, perms: set[str] | None = None, user_id: int = 1):
    user = MagicMock()
    user.id = user_id
    user.role_id = 1
    user.is_active = True
    user.role = MagicMock()
    user.role.code = role_code
    user.role.permissions = [MagicMock(code=p) for p in (perms or set())]
    user._permissions = set(perms or set())
    return user


def _admin():
    return _user("ADMIN")


def _coordinator():
    return _user("ORDER_COORDINATOR", perms={"work_orders.coordinate"})


def _region_manager():
    return _user("REGION_MANAGER", perms={"work_orders.coordinate"})


def _work_manager_no_perm():
    return _user("WORK_MANAGER", perms={"work_orders.read"})


def _supplier():
    return _user("SUPPLIER", perms={"equipment.read"})


def _accountant():
    return _user("ACCOUNTANT", perms={"invoices.read"})


# ===========================================================================
# /otp/cleanup
# ===========================================================================

class TestOtpCleanup:
    def test_admin_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.routers.otp.otp_service.cleanup_expired_tokens",
            lambda db: 5,
        )
        result = asyncio.run(cleanup_expired_tokens(_admin(), MagicMock()))
        assert result["success"] is True
        assert "Cleaned up 5" in result["message"]

    def test_accountant_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(cleanup_expired_tokens(_accountant(), MagicMock()))
        assert exc.value.status_code == 403

    def test_supplier_blocked_403(self):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(cleanup_expired_tokens(_supplier(), MagicMock()))
        assert exc.value.status_code == 403

    def test_coordinator_blocked_403(self):
        """ORDER_COORDINATOR has work_orders.coordinate but NOT
        system.settings — must be denied here."""
        with pytest.raises(HTTPException) as exc:
            asyncio.run(cleanup_expired_tokens(_coordinator(), MagicMock()))
        assert exc.value.status_code == 403


# ===========================================================================
# /work-order-coordination-logs
# ===========================================================================

class _WOCoordDB:
    def __init__(self, wo_exists=True):
        self._wo = MagicMock(id=1, deleted_at=None) if wo_exists else None

    def query(self, model):
        return self

    def filter(self, *a, **kw):
        return self

    def first(self):
        return self._wo

    def add(self, obj):
        if not getattr(obj, "id", None):
            obj.id = 99
        if not getattr(obj, "created_at", None):
            from datetime import datetime
            obj.created_at = datetime.utcnow()

    def commit(self):
        pass

    def refresh(self, obj):
        pass


class TestWOCoordinationLogs:
    def test_admin_passes(self):
        payload = CoordinationLogCreate(
            work_order_id=1, action_type="CALL", note="called supplier",
        )
        result = create_coordination_log(payload, _WOCoordDB(), _admin())
        assert result["work_order_id"] == 1

    def test_coordinator_passes(self):
        payload = CoordinationLogCreate(
            work_order_id=1, action_type="NOTE", note="follow-up",
        )
        result = create_coordination_log(payload, _WOCoordDB(), _coordinator())
        assert result["action_type"] == "NOTE"

    def test_region_manager_passes(self):
        payload = CoordinationLogCreate(
            work_order_id=1, action_type="ESCALATE", note="urgent",
        )
        result = create_coordination_log(payload, _WOCoordDB(), _region_manager())
        assert result["action_type"] == "ESCALATE"

    def test_work_manager_blocked_403(self):
        """Critical: a work manager cannot inject coordination notes
        onto WOs they don't coordinate."""
        payload = CoordinationLogCreate(
            work_order_id=1, action_type="NOTE", note="hijack attempt",
        )
        with pytest.raises(HTTPException) as exc:
            create_coordination_log(payload, _WOCoordDB(), _work_manager_no_perm())
        assert exc.value.status_code == 403

    def test_supplier_blocked_403(self):
        payload = CoordinationLogCreate(
            work_order_id=1, action_type="NOTE", note="hijack",
        )
        with pytest.raises(HTTPException) as exc:
            create_coordination_log(payload, _WOCoordDB(), _supplier())
        assert exc.value.status_code == 403

    def test_accountant_blocked_403(self):
        payload = CoordinationLogCreate(
            work_order_id=1, action_type="NOTE", note="audit",
        )
        with pytest.raises(HTTPException) as exc:
            create_coordination_log(payload, _WOCoordDB(), _accountant())
        assert exc.value.status_code == 403


# ===========================================================================
# /sync/batch — auth-only, contract verification
# ===========================================================================

class TestSyncBatch:
    def test_unknown_operation_type_recorded_as_error(self, monkeypatch):
        """Sync batch processes operations one at a time and never
        escalates auth — an unknown op_type just becomes a per-result
        error in the response, with current_user already validated by
        the FastAPI dep."""
        request = SyncBatchRequest(
            operations=[
                SyncOperation(
                    operation_type="invalid_op",
                    entity_type="worklog",
                    entity_id=None,
                    data={},
                    timestamp="2026-04-25T22:00:00",
                    client_id="c-1",
                ),
            ],
            client_id="c-1",
            last_sync="2026-04-25T20:00:00",
        )
        result = asyncio.run(sync_batch(
            request=request, db=MagicMock(), current_user=_admin(),
        ))
        assert len(result.results) == 1
        assert result.results[0].success is False
        assert "Unknown operation type" in (result.results[0].error or "")

    def test_sub_operation_uses_current_user_id_not_body(self, monkeypatch):
        """Spy: the worklog sub-handler must be called with
        current_user.id, not anything from the operation payload."""
        captured = {}

        async def fake_create_worklog(operation, db, current_user):
            captured["actor_id"] = current_user.id
            captured["operation_user_id_in_data"] = operation.data.get("user_id")
            from app.routers.sync import SyncResult
            from datetime import datetime
            return SyncResult(
                operation_type=operation.operation_type,
                entity_type=operation.entity_type,
                entity_id=99,
                success=True,
                error=None,
                server_timestamp=datetime.utcnow(),
                client_id=operation.client_id,
            )

        monkeypatch.setattr("app.routers.sync.create_worklog", fake_create_worklog)

        # Caller injects user_id=999 in the data payload; sync must NOT
        # use it — the sub-handler is called with current_user.id (42).
        request = SyncBatchRequest(
            operations=[
                SyncOperation(
                    operation_type="create_worklog",
                    entity_type="worklog",
                    entity_id=None,
                    data={
                        "work_order_id": 1,
                        "work_date": "2026-04-25",
                        "hours_worked": 8,
                        "user_id": 999,  # spoof attempt — must be ignored
                    },
                    timestamp="2026-04-25T22:00:00",
                    client_id="c-1",
                ),
            ],
            client_id="c-1",
            last_sync="2026-04-25T20:00:00",
        )
        actor = _user("WORK_MANAGER", user_id=42)
        result = asyncio.run(sync_batch(
            request=request, db=MagicMock(), current_user=actor,
        ))
        assert result.results[0].success is True
        assert captured["actor_id"] == 42, "Sub-handler must receive current_user.id"
        # The spoofed value made it INTO the payload, but the contract
        # says the sub-handler MUST ignore it (we just confirm here that
        # actor_id is the authenticated user, not the spoofed 999).
        assert captured["operation_user_id_in_data"] == 999  # caller sent it
