# app/core/audit.py
"""
Centralized business event audit logging.

Every critical business event must be logged via this module.
This creates structured records in activity_logs with consistent
action codes, metadata JSON, and entity references.
"""
import json as _json
import logging

_log = logging.getLogger("audit")


def log_business_event(
    db,
    action: str,
    entity_type: str,
    entity_id: int,
    user_id: int = None,
    description: str = None,
    metadata: dict = None,
    category: str = "operational",
):
    """Write a structured activity_log entry for any business event.

    Args:
        action: e.g. WORK_ORDER_CREATED, BUDGET_FROZEN, PROJECT_CREATED
        entity_type: e.g. work_order, worklog, invoice, budget, project
        entity_id: the DB id of the entity
        user_id: who triggered it (None for system events)
        description: Hebrew human-readable description
        metadata: arbitrary dict stored as JSON
        category: operational | financial | management | system
    """
    try:
        from sqlalchemy import text
        meta_json = _json.dumps(metadata or {}, ensure_ascii=False) if metadata else None
        db.execute(text(
            "INSERT INTO activity_logs"
            " (action, description, user_id, entity_type, entity_id,"
            "  activity_type, category, metadata_json)"
            " VALUES"
            " (:action, :desc, :uid, :etype, :eid,"
            "  'business_event', :cat, :meta)"
        ), {
            "action": action,
            "desc": description or action,
            "uid": user_id,
            "etype": entity_type,
            "eid": entity_id,
            "cat": category,
            "meta": meta_json,
        })
    except Exception as e:
        _log.warning(f"Audit log failed [{action} {entity_type}#{entity_id}]: {e}")
