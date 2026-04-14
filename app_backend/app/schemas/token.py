# /root/app_backend/app/schemas/token.py - חדש
"""Token schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TokenBase(BaseModel):
    """Base token schema."""

    token_type: str = "bearer"
    expires_in: int = 3600


class TokenCreate(TokenBase):
    """Schema for creating token."""

    access_token: str
    refresh_token: Optional[str] = None
    user_id: int
    scope: Optional[str] = None


class TokenUpdate(BaseModel):
    """Schema for updating token."""

    expires_in: Optional[int] = None
    is_active: Optional[bool] = None
    revoked_at: Optional[datetime] = None


class TokenResponse(TokenBase):
    """Token response schema."""

    access_token: str
    refresh_token: Optional[str] = None


class Token(TokenBase):
    """Full token schema."""

    id: int
    access_token: str
    refresh_token: Optional[str] = None
    user_id: int
    created_at: datetime
    expires_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    """Token payload data."""

    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    scopes: list[str] = []
