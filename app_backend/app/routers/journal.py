# app/routers/journal.py
"""
Personal journal endpoints for every user.

GET  /api/v1/users/me/journal           – activity_logs for current user (actions + personal notes)
POST /api/v1/users/me/journal/note      – add a personal note
DELETE /api/v1/users/me/journal/note/{id} – delete a personal note (own only)
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.activity_log import ActivityLog
from app.models.user import User

router = APIRouter(prefix="/users/me/journal", tags=["Journal"])

PERSONAL_NOTE_TYPE = "personal_note"


# ── Schemas ─────────────────────────────────────────────────────────────

class JournalEntry(BaseModel):
    id: int
    activity_type: str
    action: str
    description: Optional[str] = None
    details: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    created_at: datetime
    is_note: bool = False

    model_config = {"from_attributes": True}


class NoteCreate(BaseModel):
    note_text: str


# ── Endpoints ────────────────────────────────────────────────────────────

# Activity types that only ADMIN should see in their own journal
AUTH_TYPES = {'login', 'logout', 'login_failed', '2fa', 'user_login',
              'password_change', 'password_reset', '2fa_enabled', '2fa_disabled'}


@router.get("/", response_model=List[JournalEntry])
def get_journal(
    filter: Optional[str] = Query("all", description="all | actions | notes"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return the current user's journal: activity log entries + personal notes."""
    skip = (page - 1) * limit
    q = db.query(ActivityLog).filter(
        ActivityLog.user_id == current_user.id,
        ActivityLog.is_active == True,
    )

    # Non-admin users don't see login/logout entries in their journal
    role_code = ""
    if current_user.role:
        role_code = (current_user.role.code or "").upper()
    if role_code != "ADMIN":
        q = q.filter(~ActivityLog.activity_type.in_(list(AUTH_TYPES)))
        q = q.filter(~ActivityLog.action.in_(list(AUTH_TYPES)))

    if filter == "actions":
        q = q.filter(ActivityLog.activity_type != PERSONAL_NOTE_TYPE)
    elif filter == "notes":
        q = q.filter(ActivityLog.activity_type == PERSONAL_NOTE_TYPE)

    rows = q.order_by(ActivityLog.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for row in rows:
        result.append(JournalEntry(
            id=row.id,
            activity_type=row.activity_type,
            action=row.action,
            description=getattr(row, 'description', None),
            details=row.details,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            entity_name=getattr(row, 'entity_name', None),
            created_at=row.created_at,
            is_note=(row.activity_type == PERSONAL_NOTE_TYPE),
        ))
    return result


@router.post("/note", response_model=JournalEntry, status_code=status.HTTP_201_CREATED)
def add_note(
    body: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a personal note to the journal."""
    note = ActivityLog(
        user_id=current_user.id,
        activity_type=PERSONAL_NOTE_TYPE,
        action="note",
        details=body.note_text,
        category="personal",
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return JournalEntry(
        id=note.id,
        activity_type=note.activity_type,
        action=note.action,
        details=note.details,
        created_at=note.created_at,
        is_note=True,
    )


@router.delete("/note/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a personal note (only if it belongs to the current user)."""
    note = db.query(ActivityLog).filter(
        ActivityLog.id == note_id,
        ActivityLog.user_id == current_user.id,
        ActivityLog.activity_type == PERSONAL_NOTE_TYPE,
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="הערה לא נמצאה")
    note.is_active = False
    db.commit()
