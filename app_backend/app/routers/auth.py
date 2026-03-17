# app/routers/auth.py
"""Authentication endpoints."""
from typing import List, Optional
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.otp_token import OTPToken
from app.models.session import Session as UserSession
from app.models.activity_log import ActivityLog, ActivityType
from app.models.biometric_credential import BiometricCredential
from app.schemas.auth import (LoginRequest, LoginResponse, TokenRefreshRequest, TokenRefreshResponse,
                             LogoutRequest, PasswordChangeRequest, PasswordResetRequest,
                             PasswordResetConfirm, TwoFactorSetupRequest, TwoFactorSetupResponse,
                             TwoFactorVerifyRequest, TwoFactorDisableRequest, UserSessionsResponse,
                             AccountLockRequest, AccountUnlockRequest, SecurityAuditResponse,
                             PermissionCheckRequest, PermissionCheckResponse, AuthStatusResponse,
                             LoginAttemptsResponse, OTPVerificationRequest)
from app.services.activity_log_service import ActivityLogService
from app.services.auth_service import AuthService
from app.core.security import create_access_token, create_refresh_token, get_password_hash
from app.core.config import settings
from app.core.rate_limiting import check_otp_rate_limit, check_account_lock, lock_account_on_failure
import secrets
import string
import json
import hashlib
import base64
import os

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Service instances
auth_service = AuthService()
activity_log_service = ActivityLogService()

def generate_session_id() -> str:
    """Generate a random session ID"""
    return secrets.token_urlsafe(32)


@router.post("/register")
def register(
    email: str = Body(...),
    password: str = Body(...),
    full_name: str = Body(...),
    db: Session = Depends(get_db),
):
    """יצירת משתמש חדש"""
    try:
        # בדיקה אם המשתמש כבר קיים
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="משתמש כבר קיים")
        
        # יצירת תפקיד admin אם לא קיים
        admin_role = db.query(Role).filter(Role.code == "ADMIN").first()
        if not admin_role:
            admin_role = Role(
                code="ADMIN",
                name="מנהל מערכת",
                description="מנהל מערכת עם הרשאות מלאות",
                is_active=True,
                is_system_role=True
            )
            db.add(admin_role)
            db.flush()
        
        # יצירת משתמש חדש
        new_user = User(
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            first_name=full_name.split()[0] if full_name else "",
            last_name=" ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else "",
            status="ACTIVE",  # String, not Enum!
            is_active=True,
            is_verified=True,
            role_id=admin_role.id
        )
        
        db.add(new_user)
        db.commit()
        
        return {"message": "משתמש נוצר בהצלחה", "email": email}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"שגיאה ביצירת משתמש: {str(e)}")


@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Login user."""
    try:
        print(f"[SERVER] Login attempt for username: {login_data.username}")
        print(f"[SERVER] Request from IP: {request.client.host if request.client else 'Unknown'}")
        print(f"[SERVER] User-Agent: {request.headers.get('user-agent', 'Unknown')}")
        
        # Get client IP and user agent
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        result = auth_service.login(
            db=db, 
            login_data=login_data, 
            ip_address=ip_address, 
            user_agent=user_agent
        )
        
        print(f"[SERVER] Login result: {result}")
        print(f"[SERVER] Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        print(f"[SERVER] requires_2fa: {result.get('requires_2fa', 'Not found')}")
        print(f"[SERVER] user: {result.get('user', 'Not found')}")

        # Log activity - only if user object exists (not 2FA case)
        if "user" in result and result["user"]:
            try:
                activity_log_service.log_activity(
                    db=db,
                    user_id=result["user"]["id"],
                    activity_type=ActivityType.LOGIN,
                    action="user_login",
                    entity_type="user",
                    entity_id=result["user"]["id"],
                    metadata={"ip_address": ip_address, "user_agent": user_agent},
                )
            except Exception as log_error:
                logger.warning(f"Failed to log activity: {log_error}")

        return LoginResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Login error: {str(e)}\n{error_details}")
        # Return detailed error in debug mode
        if settings.DEBUG:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed. Please contact support."
            )


@router.post("/2fa/verify", response_model=LoginResponse)
def verify_2fa(
    user_id: int = Body(..., embed=True),
    code: str = Body(..., embed=True),
    backup_code: Optional[str] = Body(None, embed=True),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Verify two-factor authentication."""
    try:
        print(f"[SERVER] OTP verification attempt for user_id: {user_id}")
        print(f"[SERVER] OTP code: {code}")
        print(f"[SERVER] Backup code: {backup_code}")
        
        result = auth_service.verify_2fa(
            db=db, 
            user_id=user_id, 
            code=code, 
            backup_code=backup_code
        )
        
        print(f"[SERVER] OTP verification result: {result}")
        print(f"[SERVER] Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        print(f"[SERVER] success: {result.get('success', 'Not found')}")
        print(f"[SERVER] user: {result.get('user', 'Not found')}")

        # Log activity
        activity_log_service.log_activity(
            db=db,
            user_id=user_id,
            activity_type=ActivityType.TWO_FA_ENABLED,
            action="2fa_verified",
            entity_type="user",
            entity_id=user_id,
            metadata={"method": "totp" if not backup_code else "backup_code"},
        )

        return LoginResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh_token(
    refresh_data: TokenRefreshRequest,
    db: Session = Depends(get_db),
):
    """Refresh access token."""
    try:
        result = auth_service.refresh_token(db, refresh_data.refresh_token)
        return TokenRefreshResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
def logout(
    logout_data: LogoutRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Logout user."""
    try:
        # Get access token from Authorization header
        # In a real implementation, you would extract this from the request
        access_token = "dummy_token"  # This should be extracted from the request
        
        auth_service.logout(
            db=db, 
            access_token=access_token, 
            refresh_token=logout_data.refresh_token,
            all_sessions=logout_data.all_sessions
        )

        # Log activity
        activity_log_service.log_activity(
            db=db,
            user_id=current_user.id,
            activity_type="user_logout",
            action="user_logout",
            entity_type="user",
            entity_id=current_user.id,
            metadata={"all_sessions": logout_data.all_sessions},
        )

        return {"message": "Logged out successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/change-password")
def change_password(
    password_data: PasswordChangeRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Change user password."""
    try:
        success = auth_service.change_password(
            db=db, 
            user_id=current_user.id, 
            password_data=password_data
        )

        if success:
            # Log activity
            activity_log_service.log_activity(
                db=db,
                user_id=current_user.id,
                activity_type="password_changed",
                action="password_changed",
                entity_type="user",
                entity_id=current_user.id,
            )

            return {"message": "Password changed successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reset-password")
def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """Request password reset."""
    try:
        result = auth_service.request_password_reset(db, reset_data)
        return {"message": result}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reset-password/confirm")
def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """Confirm password reset."""
    try:
        success = auth_service.reset_password(
            db=db, 
            token=reset_data.token, 
            new_password=reset_data.new_password
        )

        if success:
            return {"message": "Password reset successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
def setup_2fa(
    setup_data: TwoFactorSetupRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Setup two-factor authentication."""
    try:
        result = auth_service.setup_2fa(
            db=db, 
            user_id=current_user.id, 
            setup_data=setup_data
        )

        # Log activity
        activity_log_service.log_activity(
            db=db,
            user_id=current_user.id,
            activity_type="2fa_setup",
            action="2fa_setup",
            entity_type="user",
            entity_id=current_user.id,
        )

        return TwoFactorSetupResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/2fa/verify-setup")
def verify_2fa_setup(
    user_id: int = Body(..., embed=True),
    code: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """Verify 2FA setup with code."""
    try:
        success = auth_service.verify_2fa_setup(db, user_id, code)
        
        if success:
            return {"message": "2FA setup verified successfully"}
        else:
            raise ValueError("Invalid verification code")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/2fa/disable")
def disable_2fa(
    disable_data: TwoFactorDisableRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Disable two-factor authentication."""
    try:
        success = auth_service.disable_2fa(
            db=db, 
            user_id=current_user.id, 
            disable_data=disable_data
        )

        if success:
            # Log activity
            activity_log_service.log_activity(
                db=db,
                user_id=current_user.id,
                action="2fa_disabled",
                entity_type="user",
                entity_id=current_user.id,
            )

            return {"message": "2FA disabled successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/sessions", response_model=UserSessionsResponse)
def get_user_sessions(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get user sessions."""
    # This would be implemented to get user sessions
    # For now, return a simple response
    return UserSessionsResponse(
        current_session={
            "session_id": "current_session_id",
            "device_info": "Current Device",
            "ip_address": "127.0.0.1",
            "user_agent": "Mozilla/5.0",
            "created_at": "2024-01-01T00:00:00Z",
            "last_activity": "2024-01-01T00:00:00Z",
            "is_active": True
        },
        other_sessions=[],
        total_sessions=1
    )


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: str,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Revoke specific session."""
    # This would be implemented to revoke a specific session
    return {"message": "Session revoked successfully"}


@router.delete("/sessions")
def revoke_all_sessions(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Revoke all user sessions."""
    # This would be implemented to revoke all user sessions
    return {"message": "All sessions revoked successfully"}


@router.get("/status", response_model=AuthStatusResponse)
def get_auth_status(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get authentication status."""
    return AuthStatusResponse(
        is_authenticated=True,
        user_id=current_user.id,
        role=current_user.role.code,
        permissions=[p.code for p in current_user.role.permissions] if current_user.role.permissions else [],
        session_expires_at=None,  # This would be calculated
        two_factor_enabled=current_user.two_factor_enabled,
        last_activity=None  # This would be retrieved from session
    )


@router.post("/check-permission", response_model=PermissionCheckResponse)
def check_permission(
    permission_data: PermissionCheckRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Check if user has specific permission."""
    # This would be implemented to check permissions
    has_permission = permission_data.permission in [p.code for p in current_user.role.permissions] if current_user.role.permissions else False
    
    return PermissionCheckResponse(
        has_permission=has_permission,
        reason=None if has_permission else "Insufficient permissions",
        required_role=None
    )


# Admin endpoints

@router.post("/admin/lock-account")
def lock_account(
    lock_data: AccountLockRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Lock user account (admin only)."""
    try:
        success = auth_service.lock_account(
            db=db, 
            user_id=lock_data.user_id, 
            reason=lock_data.reason,
            duration_hours=lock_data.duration_hours
        )

        if success:
            # Log activity
            activity_log_service.log_activity(
                db=db,
                user_id=current_user.id,
                action="account_locked",
                entity_type="user",
                entity_id=lock_data.user_id,
                details={"reason": lock_data.reason, "duration_hours": lock_data.duration_hours},
            )

            return {"message": "Account locked successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/admin/unlock-account")
def unlock_account(
    unlock_data: AccountUnlockRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Unlock user account (admin only)."""
    try:
        success = auth_service.unlock_account(
            db=db, 
            user_id=unlock_data.user_id, 
            reason=unlock_data.reason
        )

        if success:
            # Log activity
            activity_log_service.log_activity(
                db=db,
                user_id=current_user.id,
                action="account_unlocked",
                entity_type="user",
                entity_id=unlock_data.user_id,
                details={"reason": unlock_data.reason},
            )

            return {"message": "Account unlocked successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/admin/security-audit/{user_id}", response_model=SecurityAuditResponse)
def get_security_audit(
    user_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get security audit for user (admin only)."""
    # This would be implemented to get security audit data
    return SecurityAuditResponse(
        user_id=user_id,
        events=[],
        total_events=0,
        last_login=None,
        failed_attempts=0,
        account_locked=False,
        locked_until=None
    )


@router.get("/admin/login-attempts/{user_id}", response_model=LoginAttemptsResponse)
def get_login_attempts(
    user_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get login attempts for user (admin only)."""
    # This would be implemented to get login attempts
    return LoginAttemptsResponse(
        attempts=[],
        total_attempts=0,
        failed_attempts=0,
        last_attempt=None,
        account_locked=False,
        lock_expires_at=None
    )


@router.post("/send-otp")
def send_otp(
    request: dict,
    db: Session = Depends(get_db),
):
    """Send OTP to user email."""
    try:
        email = request.get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")
        
        # Check OTP rate limit
        check_otp_rate_limit(email)
        
        # Check if account is locked
        check_account_lock(email)
        
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Generate OTP token
        otp_token = auth_service._generate_otp_token(db, user.id)
        
        # For development: Print OTP to console instead of sending email
        print(f"[OTP] Code for {email}: {otp_token}")
        print(f"[INFO] OTP expires in 10 minutes")
        
        # Send OTP via email (simplified - just print to console)
        from app.core.email import send_email
        send_email(
            to=email,
            subject="OTP Code for Forest Management System",
            body=f"Your OTP code is: {otp_token}\nThis code will expire in 10 minutes."
        )
        
        return {"message": "OTP sent successfully", "email": email}
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/verify-otp", response_model=LoginResponse)
async def verify_otp(
    data: OTPVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify OTP code."""
    try:
        # Debug logging
        logger.info(f"Verifying OTP for user_id: {data.user_id}, code: {data.code}")
        
        # נקה whitespace מהקוד
        code_clean = str(data.code).strip()
        
        # חפש את ה-OTP token במסד הנתונים עם הקוד הנכון
        otp_token = db.query(OTPToken).filter(
            OTPToken.user_id == data.user_id,
            OTPToken.token == code_clean,
            OTPToken.is_used == False,
            OTPToken.is_active == True,
            OTPToken.expires_at > datetime.now()  # שימוש ב-datetime.now() במקום utcnow()
        ).first()
        
        if not otp_token:
            logger.warning(f"No valid OTP token found for user {data.user_id} with code {code_clean}")
            raise HTTPException(status_code=400, detail="Invalid or expired 2FA code")
        
        # Debug - הדפס את הטוקן מהמסד
        logger.info(f"OTP token found: {otp_token.token} for user {data.user_id}")
        
        # סמן את ה-token כמשומש
        otp_token.is_used = True
        
        # מצא את המשתמש עם eager loading של relationships
        user = db.query(User).options(
            selectinload(User.role).selectinload(Role.permissions)
        ).filter(User.id == data.user_id).first()
        
        if not user:
            logger.error(f"User {data.user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")
        
        # עדכן last_login
        user.last_login = datetime.now()
        
        # צור JWT tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # צור session
        session = UserSession(
            session_id=generate_session_id(),
            user_id=user.id,
            ip_address=None,  # תוכל להוסיף מאוחר יותר
            user_agent=None,  # תוכל להוסיף מאוחר יותר
            expires_at=datetime.now() + timedelta(days=30)
        )
        db.add(session)
        
        # רשום פעילות
        activity_log = ActivityLog(
            user_id=user.id,
            activity_type=ActivityType.LOGIN,
            action="2FA verification successful",
            entity_type="user",
            entity_id=user.id,
            session_id=session.session_id
        )
        db.add(activity_log)
        
        # שמור הכל
        db.commit()
        
        # הכן את התגובה
        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": {
                "id": user.role.id,
                "code": user.role.code,
                "name": user.role.name,
                "permissions": [
                    {"code": p.code, "name": p.name} 
                    for p in user.role.permissions
                ] if user.role else []
            } if user.role else None,
            "department_id": user.department_id,
            "region_id": user.region_id,
            "area_id": user.area_id
        }
        
        logger.info(f"OTP verification successful for user {user.id}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_data,
            requires_2fa=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OTP verification: {str(e)}")
        logger.exception(e)  # This will print the full stack trace
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/resend-otp")
async def resend_otp(
    data: OTPVerificationRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(AuthService),
):
    """Resend OTP code - always generates a new one."""
    try:
        logger.info(f"Resending OTP for user_id: {data.user_id}")
        
        # בדוק שהמשתמש קיים
        user = db.query(User).filter(User.id == data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # שליחה חוזרת - תמיד יוצר חדש
        new_otp = auth_service.resend_otp_token(db, data.user_id)
        
        logger.info(f"New OTP generated for user {data.user_id}: {new_otp}")
        
        return {
            "message": "OTP code resent successfully",
            "otp_token": new_otp,
            "user_id": data.user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending OTP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================
# Biometric Authentication (WebAuthn / Face ID / Touch ID)
# ============================================================

# Store challenges temporarily (in production, use Redis)
_biometric_challenges = {}


@router.post("/biometric/register")
async def biometric_register_start(
    http_request: Request,
    body: dict = Body(default={}),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Start biometric registration - return challenge for WebAuthn."""
    try:
        user_id = current_user.id
        username = current_user.username

        # Determine rpID from Host header (strip port), fall back to production domain
        host = http_request.headers.get("host", "forewise.co")
        rp_id = host.split(":")[0]  # strip port if present
        # Prefer explicit hostname from request body (client-sent)
        rp_id = body.get("hostname", rp_id)

        # Generate random challenge
        challenge = base64.b64encode(os.urandom(32)).decode('utf-8')

        # Store challenge temporarily
        _biometric_challenges[str(user_id)] = {
            "challenge": challenge,
            "created_at": datetime.utcnow()
        }

        return {
            "challenge": challenge,
            "rp": {
                "name": "מערכת דיווח שעות Forewise",
                "id": rp_id
            },
            "user": {
                "id": str(user_id),
                "name": username,
                "displayName": current_user.full_name or username
            }
        }

    except Exception as e:
        logger.error(f"Error starting biometric registration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/biometric/verify")
async def biometric_register_verify(
    request: dict,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Verify and store biometric credential."""
    try:
        user_id = current_user.id
        credential_id = request.get("credentialId")
        attestation_object = request.get("attestationObject")
        client_data_json = request.get("clientDataJSON")
        
        if not credential_id:
            raise HTTPException(status_code=400, detail="Missing credentialId")
        
        # Verify challenge exists
        stored_challenge = _biometric_challenges.get(str(user_id))
        if not stored_challenge:
            raise HTTPException(status_code=400, detail="No pending challenge")
        
        # Clear challenge
        del _biometric_challenges[str(user_id)]
        
        # Store the credential
        # In production, properly parse attestationObject to extract public key
        public_key = bytes(attestation_object) if attestation_object else b"demo_key"
        
        credential = BiometricCredential(
            user_id=user_id,
            credential_id=credential_id,
            public_key=public_key,
            device_name=request.get("deviceName", "Unknown Device"),
            is_active=True
        )
        db.add(credential)
        db.commit()
        
        logger.info(f"Biometric credential registered for user {user_id}")
        
        return {
            "message": "Biometric credential registered successfully",
            "credentialId": credential_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying biometric credential: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/biometric/challenge")
async def biometric_get_challenge(
    request: dict = None,
    db: Session = Depends(get_db),
):
    """Get challenge for biometric authentication."""
    try:
        # Generate random challenge
        challenge = base64.b64encode(os.urandom(32)).decode('utf-8')
        challenge_id = secrets.token_urlsafe(16)
        
        # Store challenge
        _biometric_challenges[challenge_id] = {
            "challenge": challenge,
            "created_at": datetime.utcnow()
        }
        
        # Get all active credentials
        credentials = db.query(BiometricCredential).filter(
            BiometricCredential.is_active == True
        ).all()
        
        allow_credentials = [
            {"id": cred.credential_id, "type": "public-key"}
            for cred in credentials
        ]
        
        return {
            "challenge": challenge,
            "challengeId": challenge_id,
            "allowCredentials": allow_credentials
        }
        
    except Exception as e:
        logger.error(f"Error getting biometric challenge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/biometric/authenticate")
async def biometric_authenticate(
    request: dict,
    db: Session = Depends(get_db),
):
    """Authenticate using biometric credential."""
    try:
        credential_id = request.get("credentialId")
        
        if not credential_id:
            raise HTTPException(status_code=400, detail="Missing credentialId")
        
        # Find credential
        credential = db.query(BiometricCredential).filter(
            BiometricCredential.credential_id == credential_id,
            BiometricCredential.is_active == True
        ).first()
        
        if not credential:
            raise HTTPException(status_code=404, detail="Credential not found")
        
        # Get user
        user = db.query(User).options(
            selectinload(User.role).selectinload(Role.permissions)
        ).filter(User.id == credential.user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User is inactive")
        
        # Update credential usage
        credential.last_used_at = datetime.utcnow()
        credential.sign_count += 1
        
        # Generate tokens
        access_token = create_access_token(
            subject=str(user.id),
            email=user.email,
            role=user.role.code if user.role else "USER"
        )
        refresh_token = create_refresh_token(subject=str(user.id), email=user.email)
        
        # Create session
        session = UserSession(
            user_id=user.id,
            session_id=secrets.token_urlsafe(32),
            ip_address=request.get("ip", "unknown"),
            user_agent=request.get("userAgent", "Biometric Auth"),
            is_active=True
        )
        db.add(session)
        db.commit()
        
        # Build user data
        user_data = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.code if user.role else "USER",
            "permissions": [p.code for p in user.role.permissions] if user.role and user.role.permissions else []
        }
        
        logger.info(f"Biometric authentication successful for user {user.id}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in biometric authentication: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/biometric/credentials")
async def get_biometric_credentials(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get user's registered biometric credentials."""
    credentials = db.query(BiometricCredential).filter(
        BiometricCredential.user_id == current_user.id,
        BiometricCredential.is_active == True
    ).all()
    
    return {
        "credentials": [
            {
                "id": cred.id,
                "credentialId": cred.credential_id[:20] + "...",
                "deviceName": cred.device_name,
                "createdAt": cred.created_at.isoformat() if cred.created_at else None,
                "lastUsedAt": cred.last_used_at.isoformat() if cred.last_used_at else None
            }
            for cred in credentials
        ]
    }


@router.delete("/biometric/credentials/{credential_id}")
async def delete_biometric_credential(
    credential_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a biometric credential."""
    credential = db.query(BiometricCredential).filter(
        BiometricCredential.id == credential_id,
        BiometricCredential.user_id == current_user.id
    ).first()
    
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    credential.is_active = False
    db.commit()
    
    logger.info(f"Biometric credential {credential_id} deleted for user {current_user.id}")
    
    return {"message": "Credential deleted successfully"}


# ============================================================
# NEW DEVICE-BASED AUTH ENDPOINTS (Spec v2)
# ============================================================

from app.models.device_token import DeviceToken
import uuid as uuid_module

MAX_DEVICES_PER_USER = 5
DEVICE_TOKEN_EXPIRE_DAYS = 90
OTP_MAX_ATTEMPTS = 3
OTP_RATE_LIMIT_SECONDS = 60


def _hash_value(value: str) -> str:
    """SHA-256 hex digest of a string."""
    return hashlib.sha256(value.encode()).hexdigest()


def _mask_identifier(identifier: str) -> str:
    """Mask phone/email for response."""
    if "@" in identifier:
        parts = identifier.split("@")
        local = parts[0]
        return local[:2] + "***" + local[-1:] + "@" + parts[1]
    # phone
    return identifier[:3] + "****" + identifier[-3:]


@router.post("/request-otp")
def request_otp(data: dict, db: Session = Depends(get_db)):
    """
    Step 1 — request a 6-digit OTP via phone or email.
    Spec: rate-limit 60s, hash stored, masked identifier in response.
    """
    identifier: str = data.get("identifier", "").strip()
    identifier_type: str = data.get("identifier_type", "email").strip().lower()

    if not identifier:
        raise HTTPException(status_code=400, detail="identifier is required")

    # Find user
    if identifier_type == "phone":
        user = db.query(User).filter(User.phone == identifier, User.is_active == True).first()
    else:
        user = db.query(User).filter(User.email == identifier, User.is_active == True).first()

    if not user:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="חשבון המשתמש חסום")

    # Rate limit: block if an unused OTP was sent in the last 60 seconds
    recent = db.query(OTPToken).filter(
        OTPToken.user_id == user.id,
        OTPToken.is_used == False,
        OTPToken.is_active == True,
        OTPToken.created_at > datetime.now() - timedelta(seconds=OTP_RATE_LIMIT_SECONDS),
    ).first()
    if recent:
        wait = int((recent.created_at + timedelta(seconds=OTP_RATE_LIMIT_SECONDS) - datetime.now()).total_seconds())
        raise HTTPException(status_code=429, detail=f"נשלח קוד לאחרונה. המתן {max(wait, 1)} שניות")

    # Invalidate previous unused OTPs
    db.query(OTPToken).filter(
        OTPToken.user_id == user.id,
        OTPToken.is_used == False,
        OTPToken.is_active == True,
    ).update({"is_active": False, "updated_at": datetime.now()})

    # Generate 6-digit code
    code = "".join(secrets.choice(string.digits) for _ in range(6))
    code_hash = _hash_value(code)
    expires_at = datetime.now() + timedelta(minutes=5)

    otp = OTPToken(
        user_id=user.id,
        token=code,          # kept for backward compat with existing verify-otp
        token_hash=code_hash,
        code_hash=code_hash,
        purpose="login",
        expires_at=expires_at,
        is_used=False,
        is_active=True,
        attempts=0,
    )
    db.add(otp)
    db.commit()

    # Send OTP (email for now; SMS hook ready)
    try:
        from app.core.email import send_email
        send_email(
            to=user.email,
            subject="קוד כניסה למערכת",
            body=f"קוד הכניסה שלך: {code}\nהקוד תקף ל-5 דקות.",
        )
    except Exception as e:
        logger.warning(f"Failed to send OTP email to {user.email}: {e}")

    logger.info(f"[OTP] request-otp for user {user.id} ({identifier_type}:{identifier})")
    return {
        "message": "קוד נשלח",
        "expires_in": 300,
        "masked_identifier": _mask_identifier(identifier),
    }


@router.post("/verify-otp-v2")
def verify_otp_v2(data: dict, db: Session = Depends(get_db)):
    """
    Step 2 — verify OTP + register device.
    Spec: hash compare, max 3 attempts, device_token issued.
    """
    identifier: str = data.get("identifier", "").strip()
    code: str = str(data.get("code", "")).strip()
    device_id_raw: str = data.get("device_id", "")
    device_name: str = data.get("device_name", "Unknown device")
    device_os: str = data.get("device_os", "Unknown OS")

    if not identifier or not code:
        raise HTTPException(status_code=400, detail="identifier and code are required")

    # Find user
    user = db.query(User).filter(
        (User.email == identifier) | (User.phone == identifier),
        User.is_active == True,
    ).options(selectinload(User.role).selectinload(Role.permissions)).first()

    if not user:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")

    # Find valid OTP
    otp = db.query(OTPToken).filter(
        OTPToken.user_id == user.id,
        OTPToken.is_used == False,
        OTPToken.is_active == True,
        OTPToken.expires_at > datetime.now(),
    ).order_by(OTPToken.created_at.desc()).first()

    if not otp:
        raise HTTPException(status_code=400, detail="קוד פג תוקף. בקש קוד חדש")

    if otp.attempts >= OTP_MAX_ATTEMPTS:
        otp.is_active = False
        db.commit()
        raise HTTPException(status_code=429, detail="חרגת מ-3 ניסיונות. בקש קוד חדש")

    code_hash = _hash_value(code)
    if otp.code_hash != code_hash:
        otp.attempts = (otp.attempts or 0) + 1
        remaining = OTP_MAX_ATTEMPTS - otp.attempts
        db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"קוד שגוי. נותרו {remaining} ניסיונות" if remaining > 0 else "קוד שגוי. בקש קוד חדש",
        )

    # Mark OTP used
    otp.is_used = True
    otp.is_active = False

    # Device registration
    try:
        device_id = uuid_module.UUID(device_id_raw)
    except (ValueError, AttributeError):
        device_id = uuid_module.uuid4()

    # Evict oldest device if user has too many
    active_devices = db.query(DeviceToken).filter(
        DeviceToken.user_id == user.id,
        DeviceToken.is_active == True,
    ).order_by(DeviceToken.last_used_at.asc()).all()

    if len(active_devices) >= MAX_DEVICES_PER_USER:
        active_devices[0].is_active = False
        logger.info(f"Evicted oldest device {active_devices[0].device_id} for user {user.id}")

    raw_device_token = "dvc_" + secrets.token_urlsafe(32)
    device_token_hash = _hash_value(raw_device_token)
    device_expires = datetime.now() + timedelta(days=DEVICE_TOKEN_EXPIRE_DAYS)

    # Upsert device record
    existing_device = db.query(DeviceToken).filter(
        DeviceToken.user_id == user.id,
        DeviceToken.device_id == device_id,
    ).first()

    if existing_device:
        existing_device.token_hash = device_token_hash
        existing_device.is_active = True
        existing_device.expires_at = device_expires
        existing_device.last_used_at = datetime.now()
        existing_device.device_name = device_name
        existing_device.device_os = device_os
    else:
        db.add(DeviceToken(
            user_id=user.id,
            token_hash=device_token_hash,
            device_id=device_id,
            device_name=device_name,
            device_os=device_os,
            is_active=True,
            last_used_at=datetime.now(),
            expires_at=device_expires,
        ))

    # Issue JWT tokens
    user.last_login = datetime.now()
    access_token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role.code if user.role else ""})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    db.commit()

    # Send new-device notification (async-safe best-effort)
    try:
        from app.core.email import send_email
        send_email(
            to=user.email,
            subject="כניסה ממכשיר חדש",
            body=f"כניסה חדשה למערכת ממכשיר: {device_name} ({device_os}).\nאם זה לא אתה, פנה לתמיכה מיד.",
        )
    except Exception:
        pass

    logger.info(f"[DeviceAuth] verify-otp-v2 success user={user.id} device={device_id}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "device_token": raw_device_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "name": user.full_name or user.username,
            "role": user.role.code if user.role else "",
        },
    }


@router.post("/device-login")
def device_login(data: dict, db: Session = Depends(get_db)):
    """
    Biometric re-login — client already has device_token in Keychain.
    Spec: hash lookup, expiry check, issue new tokens.
    """
    raw_token: str = data.get("device_token", "").strip()
    if not raw_token:
        raise HTTPException(status_code=401, detail="device_token is required")

    token_hash = _hash_value(raw_token)
    device = db.query(DeviceToken).filter(
        DeviceToken.token_hash == token_hash,
        DeviceToken.is_active == True,
    ).first()

    if not device:
        raise HTTPException(status_code=401, detail="מכשיר לא מזוהה או שהוסר")

    if device.expires_at < datetime.now():
        device.is_active = False
        db.commit()
        raise HTTPException(status_code=401, detail="token_expired — נדרש אימות OTP מחדש")

    user = db.query(User).options(
        selectinload(User.role).selectinload(Role.permissions)
    ).filter(User.id == device.user_id, User.is_active == True).first()

    if not user:
        raise HTTPException(status_code=401, detail="משתמש לא פעיל")

    device.last_used_at = datetime.now()
    user.last_login = datetime.now()

    access_token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role.code if user.role else ""})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    db.commit()

    logger.info(f"[DeviceAuth] device-login success user={user.id} device={device.device_id}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.delete("/devices/{device_id}")
def revoke_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Revoke a trusted device. Only the owning user can remove it.
    """
    try:
        did = uuid_module.UUID(device_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="device_id invalid UUID")

    device = db.query(DeviceToken).filter(
        DeviceToken.device_id == did,
        DeviceToken.user_id == current_user.id,
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="מכשיר לא נמצא")

    device.is_active = False
    db.commit()

    logger.info(f"[DeviceAuth] device {device_id} revoked by user {current_user.id}")
    return {"message": "מכשיר הוסר בהצלחה"}


@router.get("/devices")
def list_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all active trusted devices for the current user."""
    devices = db.query(DeviceToken).filter(
        DeviceToken.user_id == current_user.id,
        DeviceToken.is_active == True,
    ).order_by(DeviceToken.last_used_at.desc()).all()

    return [
        {
            "device_id": str(d.device_id),
            "device_name": d.device_name,
            "device_os": d.device_os,
            "last_used_at": d.last_used_at.isoformat() if d.last_used_at else None,
            "expires_at": d.expires_at.isoformat(),
        }
        for d in devices
    ]


# ============================================================
# WebAuthn — proper register/login flows (py webauthn 2.x)
# ============================================================

import os as _os

# In-memory challenge store (replace with Redis in production)
_wn_reg_challenges:   dict = {}   # user_id  → challenge bytes
_wn_login_challenges: dict = {}   # username → (challenge bytes, credential_ids)

try:
    import webauthn as _wn
    from webauthn.helpers.structs import (
        AuthenticatorSelectionCriteria,
        UserVerificationRequirement,
        AuthenticatorAttachment,
        ResidentKeyRequirement,
        PublicKeyCredentialDescriptor,
        PublicKeyCredentialType,
    )
    from webauthn.helpers.cose import COSEAlgorithmIdentifier
    import webauthn.helpers.base64url_to_bytes as _b64url
    _WN_OK = True
except Exception as _e:
    logger.warning(f"webauthn library not available: {_e}")
    _WN_OK = False


@router.post("/webauthn/register/begin")
async def webauthn_register_begin(
    http_request: Request,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Step 1 of registration: generate PublicKeyCredentialCreationOptions.
    Called while the user is already logged in.
    """
    if not _WN_OK:
        raise HTTPException(status_code=501, detail="WebAuthn library not available on server")

    rp_id = http_request.headers.get("host", "forewise.co").split(":")[0]

    # List credentials already registered for this user (to exclude)
    existing = db.query(BiometricCredential).filter(
        BiometricCredential.user_id == current_user.id,
        BiometricCredential.is_active == True,
    ).all()
    exclude_creds = [
        PublicKeyCredentialDescriptor(
            id=c.credential_id.encode() if isinstance(c.credential_id, str) else c.credential_id,
            type=PublicKeyCredentialType.PUBLIC_KEY,
        )
        for c in existing
    ]

    options = _wn.generate_registration_options(
        rp_id=rp_id,
        rp_name="מערכת ניהול יערות Forewise",
        user_name=current_user.username,
        user_display_name=current_user.full_name or current_user.username,
        user_id=str(current_user.id).encode(),
        attestation=_wn.helpers.structs.AttestationConveyancePreference.NONE,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            user_verification=UserVerificationRequirement.REQUIRED,
            resident_key=ResidentKeyRequirement.PREFERRED,
        ),
        exclude_credentials=exclude_creds,
        timeout=60000,
    )

    # Store challenge for verification
    _wn_reg_challenges[str(current_user.id)] = options.challenge

    return _wn.options_to_json(options)


@router.post("/webauthn/register/complete")
async def webauthn_register_complete(
    http_request: Request,
    body: dict = Body(...),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Step 2 of registration: verify attestation and store credential."""
    if not _WN_OK:
        raise HTTPException(status_code=501, detail="WebAuthn library not available on server")

    expected_challenge = _wn_reg_challenges.pop(str(current_user.id), None)
    if not expected_challenge:
        raise HTTPException(status_code=400, detail="No pending registration challenge")

    rp_id = http_request.headers.get("host", "forewise.co").split(":")[0]
    origin = f"https://{rp_id}"

    try:
        credential_json = _wn.helpers.structs.RegistrationCredential.parse_raw(
            __import__("json").dumps(body)
        )
        verification = _wn.verify_registration_response(
            credential=credential_json,
            expected_challenge=expected_challenge,
            expected_rp_id=rp_id,
            expected_origin=origin,
            require_user_verification=True,
        )
    except Exception as e:
        logger.error(f"WebAuthn registration verification failed: {e}")
        raise HTTPException(status_code=400, detail=f"Registration verification failed: {e}")

    # Delete any old credential for this user+device (upsert)
    db.query(BiometricCredential).filter(
        BiometricCredential.credential_id == verification.credential_id.hex(),
    ).delete()

    cred = BiometricCredential(
        user_id=current_user.id,
        credential_id=verification.credential_id.hex(),
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        device_name=body.get("device_name", None),
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(cred)
    db.commit()

    return {"ok": True, "credential_id": cred.credential_id}


@router.post("/webauthn/login/begin")
async def webauthn_login_begin(
    http_request: Request,
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Step 1 of login: generate PublicKeyCredentialRequestOptions for a username."""
    if not _WN_OK:
        raise HTTPException(status_code=501, detail="WebAuthn library not available on server")

    username: str = body.get("username", "").strip()
    if not username:
        raise HTTPException(status_code=400, detail="username required")

    user = db.query(User).filter(
        (User.username == username) | (User.email == username),
        User.is_active == True,
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")

    creds = db.query(BiometricCredential).filter(
        BiometricCredential.user_id == user.id,
        BiometricCredential.is_active == True,
    ).all()
    if not creds:
        raise HTTPException(status_code=404, detail="אין credential ביומטרי רשום למשתמש זה")

    allow_creds = [
        PublicKeyCredentialDescriptor(
            id=bytes.fromhex(c.credential_id),
            type=PublicKeyCredentialType.PUBLIC_KEY,
        )
        for c in creds
    ]

    rp_id = http_request.headers.get("host", "forewise.co").split(":")[0]

    options = _wn.generate_authentication_options(
        rp_id=rp_id,
        allow_credentials=allow_creds,
        user_verification=UserVerificationRequirement.REQUIRED,
        timeout=60000,
    )

    _wn_login_challenges[username] = {
        "challenge": options.challenge,
        "user_id": user.id,
        "creds": {c.credential_id: c for c in creds},
        "rp_id": rp_id,
    }

    return _wn.options_to_json(options)


@router.post("/webauthn/login/complete")
async def webauthn_login_complete(
    http_request: Request,
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Step 2 of login: verify assertion and return access token."""
    if not _WN_OK:
        raise HTTPException(status_code=501, detail="WebAuthn library not available on server")

    username: str = body.get("username", "").strip()
    if not username:
        raise HTTPException(status_code=400, detail="username required")

    state = _wn_login_challenges.pop(username, None)
    if not state:
        raise HTTPException(status_code=400, detail="No pending authentication challenge")

    rp_id   = state["rp_id"]
    origin  = f"https://{rp_id}"

    try:
        credential_json = _wn.helpers.structs.AuthenticationCredential.parse_raw(
            __import__("json").dumps(body.get("credential", body))
        )
        # Find the stored credential
        cred_id_hex = credential_json.raw_id.hex() if hasattr(credential_json.raw_id, 'hex') else credential_json.id
        stored_cred = state["creds"].get(cred_id_hex)
        if not stored_cred:
            # try id
            stored_cred = state["creds"].get(credential_json.id)
        if not stored_cred:
            raise HTTPException(status_code=400, detail="Credential not recognised")

        verification = _wn.verify_authentication_response(
            credential=credential_json,
            expected_challenge=state["challenge"],
            expected_rp_id=rp_id,
            expected_origin=origin,
            credential_public_key=stored_cred.public_key,
            credential_current_sign_count=stored_cred.sign_count,
            require_user_verification=True,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WebAuthn authentication verification failed: {e}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {e}")

    # Update sign count
    stored_cred.sign_count = verification.new_sign_count
    stored_cred.last_used_at = datetime.utcnow()
    db.commit()

    # Load user and build tokens
    user = db.query(User).options(
        selectinload(User.role).selectinload(Role.permissions)
    ).filter(User.id == state["user_id"]).first()

    access_token = create_access_token(
        subject=str(user.id),
        email=user.email,
        role=user.role.code if user.role else "USER",
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    user_payload = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "name": user.full_name,
        "role": {"code": user.role.code, "name": user.role.name} if user.role else None,
        "role_code": user.role.code if user.role else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_payload,
    }
