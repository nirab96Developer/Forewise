# app/schemas/token_blacklist.py
"""Token blacklist schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TokenBlacklistCreate(BaseModel):
    """Create token blacklist entry."""
    jti: str = Field(..., min_length=36, max_length=36, description="JWT ID")
    token_hash: str = Field(..., description="Token hash")
    user_id: Optional[int] = Field(None, gt=0)
    reason: str = Field(..., max_length=200, description="Blacklist reason")
    expires_at: datetime
    blacklisted_by: Optional[int] = Field(None, gt=0)


class TokenBlacklistResponse(BaseModel):
    """Token blacklist response."""
    id: int
    jti: str
    user_id: Optional[int] = None
    reason: str
    expires_at: datetime
    blacklisted_by: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenBlacklistCheck(BaseModel):
    """Check if token is blacklisted."""
    jti: str = Field(..., min_length=36, max_length=36)
    token_hash: str
