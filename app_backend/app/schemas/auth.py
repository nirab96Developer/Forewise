# app/schemas/auth.py
"""Authentication schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """Login request schema."""
    
    username: str = Field(..., description="Username or email")
    password: str = Field(..., min_length=1, description="User password")
    remember_me: bool = Field(False, description="Remember me for longer session")
    device_info: Optional[str] = Field(None, description="Device information")


class LoginResponse(BaseModel):
    """Login response schema."""
    
    access_token: Optional[str] = Field(None, description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration time in seconds")
    user: Optional[dict] = Field(None, description="User information")
    
    # 2FA fields
    requires_2fa: Optional[bool] = Field(False, description="Whether 2FA is required")
    otp_token: Optional[str] = Field(None, description="OTP token for 2FA")
    user_id: Optional[int] = Field(None, description="User ID for 2FA")


class TokenRefreshRequest(BaseModel):
    """Token refresh request schema."""
    
    refresh_token: str = Field(..., description="Refresh token")


class TokenRefreshResponse(BaseModel):
    """Token refresh response schema."""
    
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class LogoutRequest(BaseModel):
    """Logout request schema."""
    
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")
    all_sessions: bool = Field(False, description="Logout from all sessions")


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    
    email: str = Field(..., description="User email")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class TwoFactorSetupRequest(BaseModel):
    """Two-factor authentication setup request schema."""
    
    password: str = Field(..., min_length=1, description="Current password")
    method: str = Field(..., description="2FA method (totp, sms, email)")


class TwoFactorSetupResponse(BaseModel):
    """Two-factor authentication setup response schema."""
    
    qr_code: Optional[str] = Field(None, description="QR code for TOTP setup")
    secret_key: Optional[str] = Field(None, description="Secret key for manual setup")
    backup_codes: List[str] = Field(default_factory=list, description="Backup codes")
    setup_complete: bool = Field(False, description="Setup completion status")


class TwoFactorVerifyRequest(BaseModel):
    """Two-factor authentication verification request schema."""
    
    code: str = Field(..., min_length=6, max_length=6, description="2FA code")
    backup_code: Optional[str] = Field(None, description="Backup code (if 2FA code fails)")


class TwoFactorDisableRequest(BaseModel):
    """Two-factor authentication disable request schema."""
    
    password: str = Field(..., min_length=1, description="Current password")
    code: str = Field(..., min_length=6, max_length=6, description="2FA code")


class VerifyOtpRequest(BaseModel):
    """OTP verification request schema."""
    
    user_id: int = Field(..., gt=0, description="User ID")
    code: str = Field(..., min_length=6, max_length=6, description="OTP code")
    
    @field_validator('code')
    @classmethod
    def clean_code(cls, v):
        """Clean the OTP code by removing whitespace."""
        return str(v).strip()


class SessionInfo(BaseModel):
    """Session information schema."""
    
    session_id: str = Field(..., description="Session ID")
    device_info: Optional[str] = Field(None, description="Device information")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity time")
    is_active: bool = Field(True, description="Session active status")


class UserSessionsResponse(BaseModel):
    """User sessions response schema."""
    
    current_session: SessionInfo = Field(..., description="Current session")
    other_sessions: List[SessionInfo] = Field(default_factory=list, description="Other active sessions")
    total_sessions: int = Field(0, description="Total active sessions")


class AccountLockRequest(BaseModel):
    """Account lock request schema."""
    
    user_id: int = Field(..., gt=0, description="User ID to lock")
    reason: str = Field(..., min_length=1, max_length=500, description="Lock reason")
    duration_hours: Optional[int] = Field(None, gt=0, description="Lock duration in hours (permanent if not specified)")


class AccountUnlockRequest(BaseModel):
    """Account unlock request schema."""
    
    user_id: int = Field(..., gt=0, description="User ID to unlock")
    reason: str = Field(..., min_length=1, max_length=500, description="Unlock reason")


class SecurityEvent(BaseModel):
    """Security event schema."""
    
    event_type: str = Field(..., description="Event type")
    description: str = Field(..., description="Event description")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    timestamp: datetime = Field(..., description="Event timestamp")
    severity: str = Field("medium", description="Event severity (low, medium, high, critical)")


class SecurityAuditResponse(BaseModel):
    """Security audit response schema."""
    
    user_id: int = Field(..., description="User ID")
    events: List[SecurityEvent] = Field(default_factory=list, description="Security events")
    total_events: int = Field(0, description="Total events")
    last_login: Optional[datetime] = Field(None, description="Last login time")
    failed_attempts: int = Field(0, description="Failed login attempts")
    account_locked: bool = Field(False, description="Account locked status")
    locked_until: Optional[datetime] = Field(None, description="Lock expiration time")


class PermissionCheckRequest(BaseModel):
    """Permission check request schema."""
    
    permission: str = Field(..., description="Permission to check")
    resource_id: Optional[int] = Field(None, description="Resource ID (if applicable)")


class PermissionCheckResponse(BaseModel):
    """Permission check response schema."""
    
    has_permission: bool = Field(..., description="Permission granted status")
    reason: Optional[str] = Field(None, description="Reason if permission denied")
    required_role: Optional[str] = Field(None, description="Required role if applicable")


class OTPVerificationRequest(BaseModel):
    """OTP verification request schema."""
    
    email: str = Field(..., description="User email")
    code: str = Field(..., description="OTP code")
    user_id: int = Field(..., description="User ID")


class AuthStatusResponse(BaseModel):
    """Authentication status response schema."""
    
    is_authenticated: bool = Field(..., description="Authentication status")
    user_id: Optional[int] = Field(None, description="User ID if authenticated")
    role: Optional[str] = Field(None, description="User role if authenticated")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    session_expires_at: Optional[datetime] = Field(None, description="Session expiration time")
    two_factor_enabled: bool = Field(False, description="Two-factor authentication enabled")
    last_activity: Optional[datetime] = Field(None, description="Last activity time")


class LoginAttempt(BaseModel):
    """Login attempt schema."""
    
    email: str = Field(..., description="Email address")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    success: bool = Field(..., description="Login success status")
    failure_reason: Optional[str] = Field(None, description="Failure reason if unsuccessful")
    timestamp: datetime = Field(..., description="Attempt timestamp")


class LoginAttemptsResponse(BaseModel):
    """Login attempts response schema."""
    
    attempts: List[LoginAttempt] = Field(default_factory=list, description="Login attempts")
    total_attempts: int = Field(0, description="Total attempts")
    failed_attempts: int = Field(0, description="Failed attempts")
    last_attempt: Optional[datetime] = Field(None, description="Last attempt time")
    account_locked: bool = Field(False, description="Account locked status")
    lock_expires_at: Optional[datetime] = Field(None, description="Lock expiration time")
