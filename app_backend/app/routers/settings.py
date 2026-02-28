"""Settings router — general system settings (work hours, overnight guard, etc.)."""
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Annotated

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["settings"])


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert a DB row to dict."""
    if row is None:
        return {}
    keys = row._fields if hasattr(row, '_fields') else []
    return {k: v for k, v in zip(keys, row)}


@router.get("/work-hours")
def get_work_hours(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Dict[str, Any]:
    """Return work-hours settings from DB table work_hour_settings."""
    require_permission(current_user, "system.settings")
    row = db.execute(text("SELECT * FROM work_hour_settings LIMIT 1")).fetchone()
    if row is None:
        return {
            "standard_hours_per_day": 10.5,
            "net_work_hours": 9.0,
            "break_hours": 1.5,
            "start_time": "06:30",
            "end_time": "17:00",
            "break_start": "12:00",
            "break_end": "13:30",
            "overnight_guard_rate": 0,
        }
    return _row_to_dict(row)


@router.put("/work-hours")
def update_work_hours(
    payload: Dict[str, Any],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Dict[str, Any]:
    """Save work-hours settings to DB table work_hour_settings."""
    require_permission(current_user, "system.settings")
    # Build SET clause dynamically from allowed fields
    allowed = {
        "standard_hours_per_day", "net_work_hours", "break_hours",
        "start_time", "end_time", "break_start", "break_end", "overnight_guard_rate"
    }
    updates = {k: v for k, v in payload.items() if k in allowed}
    if not updates:
        return get_work_hours(db, current_user)

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["updated_at_val"] = "NOW()"
    db.execute(text(f"UPDATE work_hour_settings SET {set_clause}, updated_at = NOW()"), updates)
    db.commit()
    return get_work_hours(db, current_user)
