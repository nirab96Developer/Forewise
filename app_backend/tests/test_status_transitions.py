"""
Unit tests for status transition enforcement.
Tests the centralized state machine in app/core/enums.py.
"""
import pytest
from app.core.enums import (
    WorkOrderStatus, WO_TERMINAL, validate_wo_transition,
    WorklogStatus, WL_TERMINAL, validate_wl_transition,
)
from app.core.exceptions import ValidationException


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Work Order: Terminal state protection
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestWOTerminalProtection:
    """Terminal states must reject ALL transitions."""

    @pytest.mark.parametrize("terminal", [
        WorkOrderStatus.COMPLETED,
        WorkOrderStatus.REJECTED,
        WorkOrderStatus.CANCELLED,
        WorkOrderStatus.EXPIRED,
        WorkOrderStatus.STOPPED,
    ])
    @pytest.mark.parametrize("target", list(WorkOrderStatus))
    def test_terminal_blocks_all(self, terminal, target):
        with pytest.raises(ValidationException, match="מצב סופי"):
            validate_wo_transition(terminal, target)

    @pytest.mark.parametrize("terminal", list(WO_TERMINAL))
    def test_terminal_blocks_self(self, terminal):
        with pytest.raises(ValidationException):
            validate_wo_transition(terminal, terminal)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Work Order: Valid transitions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestWOValidTransitions:
    """Core business flow transitions must succeed."""

    def test_pending_to_distributing(self):
        validate_wo_transition("PENDING", "DISTRIBUTING")

    def test_pending_to_cancelled(self):
        validate_wo_transition("PENDING", "CANCELLED")

    def test_distributing_to_supplier_accepted(self):
        validate_wo_transition("DISTRIBUTING", "SUPPLIER_ACCEPTED_PENDING_COORDINATOR")

    def test_distributing_to_distributing(self):
        validate_wo_transition("DISTRIBUTING", "DISTRIBUTING")

    def test_distributing_to_rejected(self):
        validate_wo_transition("DISTRIBUTING", "REJECTED")

    def test_distributing_to_expired(self):
        validate_wo_transition("DISTRIBUTING", "EXPIRED")

    def test_supplier_accepted_to_approved(self):
        validate_wo_transition("SUPPLIER_ACCEPTED_PENDING_COORDINATOR", "APPROVED_AND_SENT")

    def test_supplier_accepted_to_rejected(self):
        validate_wo_transition("SUPPLIER_ACCEPTED_PENDING_COORDINATOR", "REJECTED")

    def test_approved_to_completed(self):
        validate_wo_transition("APPROVED_AND_SENT", "COMPLETED")

    def test_approved_to_stopped(self):
        validate_wo_transition("APPROVED_AND_SENT", "STOPPED")

    def test_approved_to_cancelled(self):
        validate_wo_transition("APPROVED_AND_SENT", "CANCELLED")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Work Order: Invalid transitions (skip steps)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestWOInvalidTransitions:
    """Must not allow skipping business flow steps."""

    def test_pending_cannot_complete(self):
        with pytest.raises(ValidationException):
            validate_wo_transition("PENDING", "COMPLETED")

    def test_pending_cannot_approve(self):
        with pytest.raises(ValidationException):
            validate_wo_transition("PENDING", "APPROVED_AND_SENT")

    def test_distributing_cannot_complete(self):
        with pytest.raises(ValidationException):
            validate_wo_transition("DISTRIBUTING", "COMPLETED")

    def test_supplier_accepted_cannot_complete(self):
        with pytest.raises(ValidationException):
            validate_wo_transition("SUPPLIER_ACCEPTED_PENDING_COORDINATOR", "COMPLETED")

    def test_approved_cannot_go_back_to_pending(self):
        with pytest.raises(ValidationException):
            validate_wo_transition("APPROVED_AND_SENT", "PENDING")

    def test_unknown_status_raises(self):
        with pytest.raises(ValidationException):
            validate_wo_transition("NONEXISTENT", "PENDING")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Worklog: Terminal state protection
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestWLTerminalProtection:
    """INVOICED is terminal."""

    @pytest.mark.parametrize("target", list(WorklogStatus))
    def test_invoiced_blocks_all(self, target):
        with pytest.raises(ValidationException, match="מצב סופי"):
            validate_wl_transition(WorklogStatus.INVOICED, target)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Worklog: Valid transitions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestWLValidTransitions:

    def test_pending_to_submitted(self):
        validate_wl_transition("PENDING", "SUBMITTED")

    def test_submitted_to_approved(self):
        validate_wl_transition("SUBMITTED", "APPROVED")

    def test_submitted_to_rejected(self):
        validate_wl_transition("SUBMITTED", "REJECTED")

    def test_approved_to_invoiced(self):
        validate_wl_transition("APPROVED", "INVOICED")

    def test_rejected_to_submitted(self):
        validate_wl_transition("REJECTED", "SUBMITTED")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Worklog: Invalid transitions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestWLInvalidTransitions:

    def test_pending_cannot_approve(self):
        with pytest.raises(ValidationException):
            validate_wl_transition("PENDING", "APPROVED")

    def test_pending_cannot_invoice(self):
        with pytest.raises(ValidationException):
            validate_wl_transition("PENDING", "INVOICED")

    def test_approved_cannot_go_back(self):
        with pytest.raises(ValidationException):
            validate_wl_transition("APPROVED", "PENDING")

    def test_approved_cannot_reject(self):
        with pytest.raises(ValidationException):
            validate_wl_transition("APPROVED", "REJECTED")

    def test_rejected_cannot_approve_directly(self):
        with pytest.raises(ValidationException):
            validate_wl_transition("REJECTED", "APPROVED")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Invoice: Terminal state protection
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from app.core.enums import InvoiceStatus, INV_TERMINAL, validate_inv_transition


class TestINVTerminalProtection:
    """PAID and CANCELLED are terminal."""

    @pytest.mark.parametrize("terminal", [
        InvoiceStatus.PAID,
        InvoiceStatus.CANCELLED,
    ])
    @pytest.mark.parametrize("target", list(InvoiceStatus))
    def test_terminal_blocks_all(self, terminal, target):
        with pytest.raises(ValidationException, match="מצב סופי"):
            validate_inv_transition(terminal, target)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Invoice: Valid transitions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestINVValidTransitions:

    def test_draft_to_approved(self):
        validate_inv_transition("DRAFT", "APPROVED")

    def test_draft_to_cancelled(self):
        validate_inv_transition("DRAFT", "CANCELLED")

    def test_approved_to_sent(self):
        validate_inv_transition("APPROVED", "SENT")

    def test_approved_to_paid(self):
        validate_inv_transition("APPROVED", "PAID")

    def test_approved_to_cancelled(self):
        validate_inv_transition("APPROVED", "CANCELLED")

    def test_sent_to_paid(self):
        validate_inv_transition("SENT", "PAID")

    def test_sent_to_cancelled(self):
        validate_inv_transition("SENT", "CANCELLED")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Invoice: Invalid transitions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestINVInvalidTransitions:

    def test_draft_cannot_pay(self):
        with pytest.raises(ValidationException):
            validate_inv_transition("DRAFT", "PAID")

    def test_draft_cannot_send(self):
        with pytest.raises(ValidationException):
            validate_inv_transition("DRAFT", "SENT")

    def test_sent_cannot_go_back_to_draft(self):
        with pytest.raises(ValidationException):
            validate_inv_transition("SENT", "DRAFT")

    def test_approved_cannot_go_back_to_draft(self):
        with pytest.raises(ValidationException):
            validate_inv_transition("APPROVED", "DRAFT")

    def test_unknown_status_raises(self):
        with pytest.raises(ValidationException):
            validate_inv_transition("NONEXISTENT", "DRAFT")
