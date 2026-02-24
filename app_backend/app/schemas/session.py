# app/schemas/session.py
"""Session schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SessionBase(BaseModel):
    """Base session schema."""
    user_id: int = Field(..., gt=0)
    device_id: Optional[str] = Field(None, max_length=100)


class SessionCreate(SessionBase):
    """Create session schema."""
    token_hash: str
    refresh_token_hash: Optional[str] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)
    expires_at: datetime


class SessionResponse(SessionBase):
    """Session response schema."""
    id: int
    is_active: bool
    expires_at: datetime
    last_activity: datetime
    created_at: datetime
    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[str] = None

    # Computed
    is_expired: bool = False

    model_config = ConfigDict(from_attributes=True)


class SessionList(BaseModel):
    """List of user sessions."""
    sessions: list[SessionResponse]
    active_count: int
    total_count: int
