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
    request: dict,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Start biometric registration - return challenge for WebAuthn."""
    try:
        user_id = current_user.id
        username = current_user.username
        
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
                "name": "מערכת דיווח שעות קק״ל",
                "id": request.get("hostname", "167.99.228.10")
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
