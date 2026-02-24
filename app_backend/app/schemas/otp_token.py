# app/schemas/otp_token.py
"""OTP token schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OtpType(str, Enum):
    """OTP types."""
    LOGIN = "login"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFY = "email_verify"
    PHONE_VERIFY = "phone_verify"
    TWO_FACTOR = "two_factor"


class OtpTokenRequest(BaseModel):
    """Request OTP token."""
    type: OtpType
    destination: Optional[str] = None  # email or phone


class OtpTokenVerify(BaseModel):
    """Verify OTP token."""
    token: str = Field(..., min_length=6, max_length=6)
    type: OtpType


class OtpTokenResponse(BaseModel):
    """OTP token response."""
    message: str
    expires_in_seconds: int
    destination: Optional[str] = None
