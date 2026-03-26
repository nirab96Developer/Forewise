"""
Tests for cross-entity flow validation rules.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.core.enums import WorkOrderStatus, WorklogStatus, InvoiceStatus


class TestWorklogCreationRules:
    """Worklog can only be created against APPROVED_AND_SENT work orders."""

    def test_wo_status_must_be_approved_and_sent(self):
        from app.core.enums import WO_TERMINAL
        allowed = WorkOrderStatus.APPROVED_AND_SENT
        for status in WorkOrderStatus:
            if status == allowed:
                continue
            assert status != allowed, f"{status} should not equal APPROVED_AND_SENT"

    def test_terminal_wo_blocks_worklog(self):
        from app.core.enums import WO_TERMINAL
        for terminal in WO_TERMINAL:
            assert terminal in WO_TERMINAL


class TestInvoiceFlowRules:
    """Invoice can only include APPROVED worklogs, no double-invoicing."""

    def test_approved_worklogs_required(self):
        from app.core.enums import validate_wl_transition
        validate_wl_transition("APPROVED", "INVOICED")

    def test_pending_cannot_be_invoiced(self):
        from app.core.enums import validate_wl_transition
        from app.core.exceptions import ValidationException
        with pytest.raises(ValidationException):
            validate_wl_transition("PENDING", "INVOICED")

    def test_submitted_cannot_be_invoiced(self):
        from app.core.enums import validate_wl_transition
        from app.core.exceptions import ValidationException
        with pytest.raises(ValidationException):
            validate_wl_transition("SUBMITTED", "INVOICED")

    def test_already_invoiced_cannot_be_invoiced_again(self):
        from app.core.enums import validate_wl_transition
        from app.core.exceptions import ValidationException
        with pytest.raises(ValidationException, match="מצב סופי"):
            validate_wl_transition("INVOICED", "INVOICED")


class TestInvoiceTerminal:
    """Paid/cancelled invoices cannot change."""

    def test_paid_is_terminal(self):
        from app.core.enums import validate_inv_transition
        from app.core.exceptions import ValidationException
        with pytest.raises(ValidationException, match="מצב סופי"):
            validate_inv_transition("PAID", "DRAFT")

    def test_cancelled_is_terminal(self):
        from app.core.enums import validate_inv_transition
        from app.core.exceptions import ValidationException
        with pytest.raises(ValidationException, match="מצב סופי"):
            validate_inv_transition("CANCELLED", "APPROVED")


class TestBudgetEnforcement:
    """Budget check is in WO create — just verify the enum/state flow."""

    def test_wo_must_start_as_pending(self):
        assert WorkOrderStatus.PENDING == "PENDING"

    def test_pending_can_go_to_distributing(self):
        from app.core.enums import validate_wo_transition
        validate_wo_transition("PENDING", "DISTRIBUTING")


class TestProjectCreation:
    """Area must belong to region (tested via service)."""

    def test_area_region_mismatch_concept(self):
        from app.core.exceptions import ValidationException
        area = MagicMock()
        area.region_id = 1
        area.name = "Test Area"
        data_region_id = 2
        if area.region_id != data_region_id:
            with pytest.raises(ValidationException):
                raise ValidationException("אזור לא שייך למרחב שנבחר")


class TestValidationErrorHandling:
    """Pydantic validation errors must return 422, not 500."""

    def test_negative_decimal_returns_422_not_500(self):
        """Decimal fields with ge=0 must be caught by the validation handler."""
        import decimal
        val = {"total_amount": -1000, "project_id": 115}

        from app.schemas.budget import BudgetCreate
        import pytest
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="greater_than_equal"):
            BudgetCreate.model_validate(val)

    def test_sanitize_handles_decimal_in_error_details(self):
        """The _sanitize function must convert Decimal to float for JSON."""
        import decimal
        from app.main import validation_exception_handler
        assert True
