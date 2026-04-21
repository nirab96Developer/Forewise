# app/core/enums.py
"""
Canonical status enums and transition enforcement.
This is the SINGLE source of truth for all entity statuses.
"""
import json as _json
from enum import Enum
from typing import Dict, FrozenSet, Optional

from app.core.exceptions import ValidationException


# ---------------------------------------------------------------------------
# Work Order
# ---------------------------------------------------------------------------

class WorkOrderStatus(str, Enum):
    PENDING = "PENDING"
    DISTRIBUTING = "DISTRIBUTING"
    SUPPLIER_ACCEPTED_PENDING_COORDINATOR = "SUPPLIER_ACCEPTED_PENDING_COORDINATOR"
    APPROVED_AND_SENT = "APPROVED_AND_SENT"
    IN_PROGRESS = "IN_PROGRESS"
    ACTIVE = "ACTIVE"
    NEEDS_RE_COORDINATION = "NEEDS_RE_COORDINATION"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    STOPPED = "STOPPED"


WO_TERMINAL: FrozenSet[str] = frozenset({
    WorkOrderStatus.COMPLETED,
    WorkOrderStatus.REJECTED,
    WorkOrderStatus.CANCELLED,
    WorkOrderStatus.EXPIRED,
    WorkOrderStatus.STOPPED,
})

# Statuses where the work is being executed in the field
# (after coordinator approval, before completion). Any of these allows
# field-side operations: equipment scan, worklog reporting.
WO_EXECUTION: FrozenSet[str] = frozenset({
    WorkOrderStatus.APPROVED_AND_SENT,
    WorkOrderStatus.IN_PROGRESS,
    WorkOrderStatus.ACTIVE,
})

WO_TRANSITIONS: Dict[str, FrozenSet[str]] = {
    WorkOrderStatus.PENDING: frozenset({
        WorkOrderStatus.DISTRIBUTING,
        WorkOrderStatus.CANCELLED,
    }),
    WorkOrderStatus.DISTRIBUTING: frozenset({
        WorkOrderStatus.DISTRIBUTING,
        WorkOrderStatus.SUPPLIER_ACCEPTED_PENDING_COORDINATOR,
        WorkOrderStatus.REJECTED,
        WorkOrderStatus.CANCELLED,
        WorkOrderStatus.EXPIRED,
    }),
    WorkOrderStatus.SUPPLIER_ACCEPTED_PENDING_COORDINATOR: frozenset({
        WorkOrderStatus.APPROVED_AND_SENT,
        WorkOrderStatus.REJECTED,
        WorkOrderStatus.CANCELLED,
    }),
    WorkOrderStatus.APPROVED_AND_SENT: frozenset({
        WorkOrderStatus.IN_PROGRESS,
        WorkOrderStatus.ACTIVE,
        WorkOrderStatus.NEEDS_RE_COORDINATION,
        WorkOrderStatus.COMPLETED,
        WorkOrderStatus.CANCELLED,
        WorkOrderStatus.STOPPED,
    }),
    WorkOrderStatus.IN_PROGRESS: frozenset({
        WorkOrderStatus.ACTIVE,
        WorkOrderStatus.NEEDS_RE_COORDINATION,
        WorkOrderStatus.COMPLETED,
        WorkOrderStatus.CANCELLED,
        WorkOrderStatus.STOPPED,
    }),
    WorkOrderStatus.ACTIVE: frozenset({
        WorkOrderStatus.IN_PROGRESS,
        WorkOrderStatus.NEEDS_RE_COORDINATION,
        WorkOrderStatus.COMPLETED,
        WorkOrderStatus.CANCELLED,
        WorkOrderStatus.STOPPED,
    }),
    # Coordinator must re-decide: send to next supplier, override with admin,
    # or cancel. Field operations (scan / worklog) are blocked while here.
    WorkOrderStatus.NEEDS_RE_COORDINATION: frozenset({
        WorkOrderStatus.DISTRIBUTING,        # coordinator re-distributes
        WorkOrderStatus.APPROVED_AND_SENT,    # admin override (different equipment OK)
        WorkOrderStatus.IN_PROGRESS,          # admin override + already-scanned
        WorkOrderStatus.CANCELLED,
    }),
    WorkOrderStatus.COMPLETED: frozenset(),
    WorkOrderStatus.REJECTED: frozenset(),
    WorkOrderStatus.CANCELLED: frozenset(),
    WorkOrderStatus.EXPIRED: frozenset(),
    WorkOrderStatus.STOPPED: frozenset(),
}

WO_LABELS: Dict[str, str] = {
    WorkOrderStatus.PENDING: "ממתין",
    WorkOrderStatus.DISTRIBUTING: "בהפצה לספקים",
    WorkOrderStatus.SUPPLIER_ACCEPTED_PENDING_COORDINATOR: "ספק אישר - ממתין לאישור",
    WorkOrderStatus.APPROVED_AND_SENT: "אושר ונשלח",
    WorkOrderStatus.IN_PROGRESS: "בביצוע",
    WorkOrderStatus.ACTIVE: "פעיל בשטח",
    WorkOrderStatus.NEEDS_RE_COORDINATION: "ממתין לבדיקת מתאם — סוג כלי שגוי",
    WorkOrderStatus.COMPLETED: "הושלם",
    WorkOrderStatus.REJECTED: "נדחה",
    WorkOrderStatus.CANCELLED: "בוטל",
    WorkOrderStatus.EXPIRED: "פג תוקף",
    WorkOrderStatus.STOPPED: "הופסק",
}

MAX_ROTATION_ATTEMPTS = 10


def validate_wo_transition(current: str, target: str) -> None:
    """Validate a work order status transition. Raises ValidationException on invalid."""
    current_upper = (current or "").upper()
    target_upper = (target or "").upper()

    if current_upper in WO_TERMINAL:
        label = WO_LABELS.get(current_upper, current)
        raise ValidationException(
            f"לא ניתן לשנות סטטוס של הזמנה במצב סופי ({label})"
        )

    allowed = WO_TRANSITIONS.get(current_upper)
    if allowed is None:
        raise ValidationException(f"סטטוס נוכחי לא תקין: {current}")
    if target_upper not in allowed:
        current_label = WO_LABELS.get(current_upper, current)
        target_label = WO_LABELS.get(target_upper, target)
        raise ValidationException(
            f"מעבר סטטוס לא חוקי: {current_label} -> {target_label}"
        )


# ---------------------------------------------------------------------------
# Worklog
# ---------------------------------------------------------------------------

class WorklogStatus(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    INVOICED = "INVOICED"


WL_TERMINAL: FrozenSet[str] = frozenset({
    WorklogStatus.INVOICED,
})

WL_TRANSITIONS: Dict[str, FrozenSet[str]] = {
    WorklogStatus.PENDING: frozenset({
        WorklogStatus.SUBMITTED,
    }),
    WorklogStatus.SUBMITTED: frozenset({
        WorklogStatus.APPROVED,
        WorklogStatus.REJECTED,
    }),
    WorklogStatus.APPROVED: frozenset({
        WorklogStatus.INVOICED,
    }),
    WorklogStatus.REJECTED: frozenset({
        WorklogStatus.SUBMITTED,
    }),
    WorklogStatus.INVOICED: frozenset(),
}

WL_LABELS: Dict[str, str] = {
    WorklogStatus.PENDING: "ממתין",
    WorklogStatus.SUBMITTED: "הוגש",
    WorklogStatus.APPROVED: "אושר",
    WorklogStatus.REJECTED: "נדחה",
    WorklogStatus.INVOICED: "הופק חשבון",
}


def validate_wl_transition(current: str, target: str) -> None:
    """Validate a worklog status transition."""
    current_upper = (current or "").upper()
    target_upper = (target or "").upper()

    if current_upper in WL_TERMINAL:
        label = WL_LABELS.get(current_upper, current)
        raise ValidationException(
            f"לא ניתן לשנות סטטוס של דיווח במצב סופי ({label})"
        )

    allowed = WL_TRANSITIONS.get(current_upper)
    if allowed is None:
        raise ValidationException(f"סטטוס דיווח נוכחי לא תקין: {current}")
    if target_upper not in allowed:
        current_label = WL_LABELS.get(current_upper, current)
        target_label = WL_LABELS.get(target_upper, target)
        raise ValidationException(
            f"מעבר סטטוס דיווח לא חוקי: {current_label} -> {target_label}"
        )


# ---------------------------------------------------------------------------
# Invoice
# ---------------------------------------------------------------------------

class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    SENT = "SENT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


INV_TERMINAL: FrozenSet[str] = frozenset({
    InvoiceStatus.PAID,
    InvoiceStatus.CANCELLED,
})

INV_TRANSITIONS: Dict[str, FrozenSet[str]] = {
    InvoiceStatus.DRAFT: frozenset({
        InvoiceStatus.APPROVED,
        InvoiceStatus.CANCELLED,
    }),
    InvoiceStatus.APPROVED: frozenset({
        InvoiceStatus.SENT,
        InvoiceStatus.PAID,
        InvoiceStatus.CANCELLED,
    }),
    InvoiceStatus.SENT: frozenset({
        InvoiceStatus.PAID,
        InvoiceStatus.CANCELLED,
    }),
    InvoiceStatus.PAID: frozenset(),
    InvoiceStatus.CANCELLED: frozenset(),
}

INV_LABELS: Dict[str, str] = {
    InvoiceStatus.DRAFT: "טיוטה",
    InvoiceStatus.APPROVED: "מאושר",
    InvoiceStatus.SENT: "נשלח",
    InvoiceStatus.PAID: "שולם",
    InvoiceStatus.CANCELLED: "בוטל",
}


def validate_inv_transition(current: str, target: str) -> None:
    """Validate an invoice status transition."""
    current_upper = (current or "").upper()
    target_upper = (target or "").upper()

    if current_upper in INV_TERMINAL:
        label = INV_LABELS.get(current_upper, current)
        raise ValidationException(
            f"לא ניתן לשנות סטטוס של חשבונית במצב סופי ({label})"
        )

    allowed = INV_TRANSITIONS.get(current_upper)
    if allowed is None:
        raise ValidationException(f"סטטוס חשבונית נוכחי לא תקין: {current}")
    if target_upper not in allowed:
        current_label = INV_LABELS.get(current_upper, current)
        target_label = INV_LABELS.get(target_upper, target)
        raise ValidationException(
            f"מעבר סטטוס חשבונית לא חוקי: {current_label} -> {target_label}"
        )


# ---------------------------------------------------------------------------
# Audit helper
# ---------------------------------------------------------------------------

def log_status_change(
    db,
    entity_type: str,
    entity_id: int,
    old_status: str,
    new_status: str,
    user_id: Optional[int] = None,
    description: Optional[str] = None,
    reason: Optional[str] = None,
    source: Optional[str] = None,
):
    """Write a structured audit record for every status transition.

    Stores structured JSON in metadata_json with:
      old_status, new_status, reason, source
    """
    try:
        from sqlalchemy import text
        desc = description or f"{old_status} -> {new_status}"
        old_val = old_status.value if hasattr(old_status, 'value') else str(old_status)
        new_val = new_status.value if hasattr(new_status, 'value') else str(new_status)
        meta = _json.dumps({
            "old_status": old_val,
            "new_status": new_val,
            "reason": reason or desc,
            "source": source or "service",
        }, ensure_ascii=False)
        db.execute(text(
            "INSERT INTO activity_logs"
            " (action, description, user_id, entity_type, entity_id,"
            "  activity_type, category, metadata_json)"
            " VALUES"
            " (:action, :desc, :uid, :etype, :eid,"
            "  'status_change', 'operational', :meta)"
        ), {
            "action": f"STATUS_CHANGE_{entity_type.upper()}",
            "desc": desc,
            "uid": user_id,
            "etype": entity_type,
            "eid": entity_id,
            "meta": meta,
        })
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
            f"Failed to log status change: {entity_type}#{entity_id} "
            f"{old_status} -> {new_status}"
        )
