"""
Tests for audit logging coverage on critical business events.

Verifies that the audit module works correctly and that
the log_business_event function produces valid records.
"""
import pytest
from unittest.mock import MagicMock, patch, call
from app.core.audit import log_business_event
from app.core.enums import (
    log_status_change,
    WorkOrderStatus, WorklogStatus, InvoiceStatus,
)


class TestLogBusinessEvent:

    def test_creates_activity_log_record(self):
        db = MagicMock()
        log_business_event(
            db, "WORK_ORDER_CREATED", "work_order", 42,
            user_id=1,
            description="Test WO created",
            metadata={"project_id": 10},
            category="operational",
        )
        db.execute.assert_called_once()
        call_args = db.execute.call_args
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]
        assert params["action"] == "WORK_ORDER_CREATED"
        assert params["etype"] == "work_order"
        assert params["eid"] == 42
        assert params["uid"] == 1

    def test_handles_db_failure_gracefully(self):
        db = MagicMock()
        db.execute.side_effect = Exception("DB error")
        log_business_event(db, "TEST", "test", 1)

    def test_metadata_serialized_as_json(self):
        db = MagicMock()
        log_business_event(
            db, "TEST", "test", 1,
            metadata={"key": "value", "num": 42},
        )
        call_args = db.execute.call_args
        params = call_args[0][1]
        import json
        meta = json.loads(params["meta"])
        assert meta["key"] == "value"
        assert meta["num"] == 42


class TestLogStatusChange:

    def test_status_change_includes_metadata(self):
        db = MagicMock()
        log_status_change(
            db, "work_order", 1, "PENDING", "DISTRIBUTING",
            user_id=5, reason="test reason", source="user",
        )
        db.execute.assert_called_once()
        call_args = db.execute.call_args
        params = call_args[0][1]
        assert params["action"] == "STATUS_CHANGE_WORK_ORDER"
        import json
        meta = json.loads(params["meta"])
        assert meta["old_status"] == "PENDING"
        assert meta["new_status"] == "DISTRIBUTING"
        assert meta["reason"] == "test reason"
        assert meta["source"] == "user"

    def test_enum_values_serialized_cleanly(self):
        db = MagicMock()
        log_status_change(
            db, "invoice", 1,
            InvoiceStatus.DRAFT, InvoiceStatus.APPROVED,
            user_id=1, reason="test", source="user",
        )
        call_args = db.execute.call_args
        params = call_args[0][1]
        import json
        meta = json.loads(params["meta"])
        assert meta["old_status"] == "DRAFT"
        assert meta["new_status"] == "APPROVED"


class TestAuditCoverage:
    """Verify that critical code paths include audit calls."""

    def test_wo_service_has_create_audit(self):
        import inspect
        from app.services.work_order_service import WorkOrderService
        src = inspect.getsource(WorkOrderService.create_work_order)
        assert "log_business_event" in src or "WORK_ORDER_CREATED" in src

    def test_invoice_service_has_create_audit(self):
        import inspect
        from app.services.invoice_service import InvoiceService
        src = inspect.getsource(InvoiceService.create)
        assert "log_business_event" in src or "INVOICE_CREATED" in src

    def test_project_service_has_create_audit(self):
        import inspect
        from app.services.project_service import ProjectService
        src = inspect.getsource(ProjectService.create)
        assert "log_business_event" in src or "PROJECT_CREATED" in src

    def test_budget_freeze_has_audit(self):
        import inspect
        from app.services.budget_service import freeze_budget_for_work_order
        src = inspect.getsource(freeze_budget_for_work_order)
        assert "log_business_event" in src or "BUDGET_FROZEN" in src

    def test_budget_release_has_audit(self):
        import inspect
        from app.services.budget_service import release_budget_freeze
        src = inspect.getsource(release_budget_freeze)
        assert "log_business_event" in src or "BUDGET_RELEASED" in src

    def test_wo_approve_has_status_audit(self):
        import inspect
        from app.services.work_order_service import WorkOrderService
        src = inspect.getsource(WorkOrderService.approve)
        assert "log_status_change" in src

    def test_wl_approve_has_status_audit(self):
        import inspect
        from app.services.worklog_service import WorklogService
        src = inspect.getsource(WorklogService.approve)
        assert "log_status_change" in src

    def test_invoice_approve_has_status_audit(self):
        import inspect
        from app.services.invoice_service import InvoiceService
        src = inspect.getsource(InvoiceService.approve)
        assert "log_status_change" in src
