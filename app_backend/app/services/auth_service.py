# app/services/auth_service.py
"""Authentication service."""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.config import settings
from app.core.security import verify_password, get_password_hash
from app.core.email import send_reset_password_email
from app.models.user import User
from app.models.session import Session as UserSession
from app.models.otp_token import OTPToken
from app.models.token_blacklist import TokenBlacklist
from app.schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    TwoFactorSetupRequest,
    TwoFactorVerifyRequest,
    TwoFactorDisableRequest,
)


class AuthService:
    """Service for authentication operations."""

    def __init__(self):
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        self.REFRESH_TOKEN_EXPIRE_DAYS = 7

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return verify_password(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return get_password_hash(password)

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token with JTI."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        # Add JTI if not present
        if "jti" not in to_encode:
            to_encode["jti"] = secrets.token_urlsafe(32)

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_jwt

    def create_refresh_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token with JTI."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)

        # Add JTI if not present
        if "jti" not in to_encode:
            to_encode["jti"] = secrets.token_urlsafe(32)

        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_jwt

    def verify_token(
        self, token: str, token_type: str = "access"
    ) -> Optional[Dict[str, Any]]:
        """Verify JWT token."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload.get("type") != token_type:
                return None
            return payload
        except JWTError:
            return None

    def is_token_blacklisted(self, db: Session, token: str) -> bool:
        """Check if token is blacklisted by JTI or token hash."""
        try:
            # Try to decode token to get JTI
            payload = self.verify_token(token)
            if payload and "jti" in payload:
                jti = payload["jti"]
                blacklisted = (
                    db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
                )
                if blacklisted:
                    return True

            # Fallback: check by token hash
            import hashlib

            token_hash = hashlib.sha256(token.encode()).hexdigest()
            blacklisted = (
                db.query(TokenBlacklist)
                .filter(TokenBlacklist.token_hash == token_hash)
                .first()
            )
            return blacklisted is not None
        except Exception:
            # If token is invalid, consider it not blacklisted (will fail verification anyway)
            return False

    def blacklist_token(
        self,
        db: Session,
        token: str,
        reason: str = "logout",
        user_id: Optional[int] = None,
    ) -> None:
        """Add token to blacklist."""
        try:
            # Decode token to get JTI and expiration
            payload = self.verify_token(token)
            if not payload:
                # If token is invalid, we can't blacklist it properly
                return

            jti = payload.get("jti")
            if not jti:
                # Generate JTI if not present
                jti = secrets.token_urlsafe(32)

            # Get expiration from token
            expires_at = datetime.utcnow() + timedelta(days=7)  # Default
            if "exp" in payload:
                expires_at = datetime.fromtimestamp(payload["exp"])

            # Create token hash
            import hashlib

            token_hash = hashlib.sha256(token.encode()).hexdigest()

            # Get user_id from token if not provided
            if not user_id and "sub" in payload:
                try:
                    user_id = int(payload["sub"])
                except (ValueError, TypeError):
                    pass

            blacklist_entry = TokenBlacklist(
                jti=jti,
                token_hash=token_hash,
                reason=reason,
                expires_at=expires_at,
                user_id=user_id,
            )
            db.add(blacklist_entry)
            db.commit()
        except Exception as e:
            # Log error but don't fail the operation
            db.rollback()
            print(f"Warning: Failed to blacklist token: {e}")

    def authenticate_user(
        self, db: Session, username: str, password: str
    ) -> Optional[User]:
        """Authenticate user with username/email and password."""
        # Try to find user by username or email
        user = (
            db.query(User)
            .filter(
                and_(
                    or_(User.username == username, User.email == username),
                    User.is_active == True,
                )
            )
            .first()
        )

        if not user:
            return None

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            print(f"[AUTH_SERVICE] Account locked for user: {user.email}")
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        return user

    def login(
        self,
        db: Session,
        login_data: LoginRequest,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Dict[str, Any]:
        """Login user and create session."""
        print(f"[AUTH_SERVICE] Starting login for username: {login_data.username}")

        user = self.authenticate_user(db, login_data.username, login_data.password)

        if not user:
            print(
                f"[AUTH_SERVICE] Authentication failed for username: {login_data.username}"
            )
            raise ValueError("Invalid username or password")

        print(f"[AUTH_SERVICE] User authenticated: {user.email} (ID: {user.id})")
        print(f"[AUTH_SERVICE] User 2FA enabled: {user.two_factor_enabled}")

        # Check if 2FA is required
        if user.two_factor_enabled:
            print(f"[AUTH_SERVICE] 2FA required for user: {user.email}")

            # לבטחות מידע מקסימלית - תמיד ניצור OTP חדש
            print(f"[AUTH_SERVICE] Generating new OTP for security...")

            # סמן את כל ה-OTP הקיימים כמשומשים
            existing_tokens = (
                db.query(OTPToken)
                .filter(
                    OTPToken.user_id == user.id,
                    OTPToken.purpose == "2fa_verification",
                    OTPToken.is_used == False,
                    OTPToken.is_active == True,
                )
                .all()
            )

            for token in existing_tokens:
                token.is_used = True
                print(
                    f"[AUTH_SERVICE] Marked old OTP {token.token} as used for security"
                )

            db.commit()

            # צור OTP חדש
            otp_token = self._generate_otp_token(db, user.id)
            print(f"[AUTH_SERVICE] Generated new OTP token: {otp_token}")
            result = {
                "requires_2fa": True,
                "otp_token": otp_token,
                "user_id": user.id,
                "message": "New OTP generated for security",
            }
            print(f"[AUTH_SERVICE] Returning new OTP: {result}")
            return result

        # Create tokens
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.code}
        )
        refresh_days = 30 if login_data.remember_me else 1
        refresh_token = self.create_refresh_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=timedelta(days=refresh_days),
        )

        # Create session
        session = self._create_session(
            db=db,
            user_id=user.id,
            device_info=login_data.device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_days=refresh_days,
        )

        # Update last login
        user.last_login = datetime.now()
        db.commit()

        # Get permissions safely
        permissions = []
        if user.role and hasattr(user.role, "permissions") and user.role.permissions:
            try:
                permissions = [p.code for p in user.role.permissions]
            except Exception as e:
                print(f"[AUTH_SERVICE] Error getting permissions: {e}")
                permissions = []

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.code if user.role else None,
                "permissions": permissions,
            },
        }

    def verify_2fa(
        self, db: Session, user_id: int, code: str, backup_code: str = None
    ) -> Dict[str, Any]:
        """Verify 2FA code."""
        print(f"[AUTH_SERVICE] Starting 2FA verification for user_id: {user_id}")
        print(f"[AUTH_SERVICE] Code provided: {code}")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"[AUTH_SERVICE] User not found: {user_id}")
            raise ValueError("User not found")

        print(f"[AUTH_SERVICE] User found: {user.email} (ID: {user.id})")
        print(f"[AUTH_SERVICE] User 2FA enabled: {user.two_factor_enabled}")

        if not user.two_factor_enabled:
            print(f"[AUTH_SERVICE] 2FA not enabled for user: {user.email}")
            raise ValueError("2FA not enabled")

        # Check OTP token
        print(f"[AUTH_SERVICE] Looking for OTP token for user_id: {user_id}")
        otp_token = (
            db.query(OTPToken)
            .filter(
                and_(
                    OTPToken.user_id == user_id,
                    OTPToken.purpose == "2fa_verification",
                    OTPToken.is_used == False,
                    OTPToken.is_active == True,
                    OTPToken.expires_at > datetime.now(),
                )
            )
            .order_by(OTPToken.id.desc())
            .first()
        )

        if not otp_token:
            print(f"[AUTH_SERVICE] No valid OTP token found for user_id: {user_id}")
            raise ValueError("Invalid or expired 2FA token")

        print(f"[AUTH_SERVICE] OTP token found: {otp_token.token}")
        print(f"[AUTH_SERVICE] Token expires at: {otp_token.expires_at}")
        print(f"[AUTH_SERVICE] Current time: {datetime.now()}")

        # Verify code (simplified - in real implementation, use TOTP library)
        if code != otp_token.token:
            print(
                f"[AUTH_SERVICE] Code mismatch. Expected: {otp_token.token}, Got: {code}"
            )
            raise ValueError("Invalid 2FA code")

        print(f"[AUTH_SERVICE] Code verified successfully!")

        # Mark token as used
        otp_token.is_used = True

        # Create tokens
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.code}
        )
        refresh_token = self.create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )

        # Create session
        session = self._create_session(db=db, user_id=user.id)

        # Update last login
        user.last_login = datetime.now()
        db.commit()

        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.code,
                "permissions": [p.code for p in user.role.permissions]
                if (
                    user.role
                    and hasattr(user.role, "permissions")
                    and user.role.permissions
                )
                else [],
            },
        }

    def refresh_token(self, db: Session, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token."""
        # Verify refresh token
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            raise ValueError("Invalid refresh token")

        # Check if token is blacklisted
        if self.is_token_blacklisted(db, refresh_token):
            raise ValueError("Token is blacklisted")

        # Get user
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        # Create new access token
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.code}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    def logout(
        self,
        db: Session,
        access_token: str,
        refresh_token: str = None,
        all_sessions: bool = False,
    ) -> None:
        """Logout user."""
        # Blacklist access token
        self.blacklist_token(db, access_token, "logout")

        # Blacklist refresh token if provided
        if refresh_token:
            self.blacklist_token(db, refresh_token, "logout")

        # If logout from all sessions, blacklist all user tokens
        if all_sessions:
            payload = self.verify_token(access_token)
            if payload:
                user_id = payload.get("sub")
                # In a real implementation, you would blacklist all user tokens
                # This is a simplified version
                pass

    def change_password(
        self, db: Session, user_id: int, password_data: PasswordChangeRequest
    ) -> bool:
        """Change user password."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Verify current password
        if not self.verify_password(password_data.current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        # Update password
        user.password_hash = self.get_password_hash(password_data.new_password)
        user.updated_at = datetime.utcnow()
        db.commit()

        return True

    def request_password_reset(
        self, db: Session, reset_data: PasswordResetRequest
    ) -> str:
        """Request password reset."""
        user = db.query(User).filter(User.email == reset_data.email).first()
        if not user:
            # Don't reveal if user exists
            return "If the email exists, a reset link has been sent"

        # Invalidate previous active reset tokens for one-time usage hardening.
        db.query(OTPToken).filter(
            OTPToken.user_id == user.id,
            OTPToken.purpose == "password_reset",
            OTPToken.is_used == False,
            OTPToken.is_active == True,
        ).update({"is_used": True, "used_at": datetime.utcnow()})

        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(reset_token.encode()).hexdigest()

        # Create OTP token for password reset
        otp_token = OTPToken(
            user_id=user.id,
            token=None,
            token_hash=token_hash,
            purpose="password_reset",
            expires_at=datetime.utcnow()
            + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS),
            is_used=False,
            is_active=True,
            version=1,
        )
        db.add(otp_token)
        db.commit()

        reset_link = (
            f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={reset_token}"
        )
        send_reset_password_email(email=user.email, token=reset_link)

        return "If the email exists, a reset link has been sent"

    def reset_password(self, db: Session, token: str, new_password: str) -> bool:
        """Reset password with token."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        otp_token = (
            db.query(OTPToken)
            .filter(
                and_(
                    OTPToken.token_hash == token_hash,
                    OTPToken.purpose == "password_reset",
                    OTPToken.is_used == False,
                    OTPToken.expires_at > datetime.utcnow(),
                )
            )
            .first()
        )

        if not otp_token:
            raise ValueError("Invalid or expired reset token")

        # Update password
        user = db.query(User).filter(User.id == otp_token.user_id).first()
        if not user:
            raise ValueError("User not found")

        user.password_hash = self.get_password_hash(new_password)
        user.updated_at = datetime.utcnow()

        # Mark token as used
        otp_token.is_used = True
        otp_token.used_at = datetime.utcnow()
        otp_token.token = None

        db.commit()
        return True

    def setup_2fa(
        self, db: Session, user_id: int, setup_data: TwoFactorSetupRequest
    ) -> Dict[str, Any]:
        """Setup two-factor authentication."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Verify password
        if not self.verify_password(setup_data.password, user.password_hash):
            raise ValueError("Password is incorrect")

        # Generate secret key for TOTP
        secret_key = secrets.token_urlsafe(32)

        # Generate backup codes
        backup_codes = [secrets.token_urlsafe(8) for _ in range(10)]

        # Store 2FA data (simplified - in real implementation, use proper TOTP)
        user.two_factor_secret = secret_key
        user.two_factor_backup_codes = backup_codes
        user.two_factor_enabled = True
        user.updated_at = datetime.utcnow()

        db.commit()

        return {
            "qr_code": f"otpauth://totp/{user.email}?secret={secret_key}",
            "secret_key": secret_key,
            "backup_codes": backup_codes,
            "setup_complete": True,
        }

    def verify_2fa_setup(self, db: Session, user_id: int, code: str) -> bool:
        """Verify 2FA setup with code."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # In a real implementation, verify TOTP code
        # For now, accept any 6-digit code
        if len(code) == 6 and code.isdigit():
            return True

        return False

    def disable_2fa(
        self, db: Session, user_id: int, disable_data: TwoFactorDisableRequest
    ) -> bool:
        """Disable two-factor authentication."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Verify password
        if not self.verify_password(disable_data.password, user.password_hash):
            raise ValueError("Password is incorrect")

        # Verify 2FA code
        if not self.verify_2fa_setup(db, user_id, disable_data.code):
            raise ValueError("Invalid 2FA code")

        # Disable 2FA
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.two_factor_backup_codes = None
        user.updated_at = datetime.utcnow()

        db.commit()
        return True

    def lock_account(
        self, db: Session, user_id: int, reason: str, duration_hours: int = None
    ) -> bool:
        """Lock user account."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        if duration_hours:
            user.locked_until = datetime.utcnow() + timedelta(hours=duration_hours)
        else:
            user.locked_until = datetime.utcnow() + timedelta(
                days=365
            )  # Permanent lock

        user.lock_reason = reason
        user.updated_at = datetime.utcnow()

        # Invalidate all user sessions
        db.query(UserSession).filter(UserSession.user_id == user_id).update(
            {"is_active": False}
        )

        db.commit()
        return True

    def unlock_account(self, db: Session, user_id: int, reason: str) -> bool:
        """Unlock user account."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        user.locked_until = None
        user.lock_reason = None
        user.updated_at = datetime.utcnow()

        db.commit()
        return True

    def _create_session(
        self,
        db: Session,
        user_id: int,
        device_info: str = None,
        ip_address: str = None,
        user_agent: str = None,
        expires_days: int = 30,
    ) -> UserSession:
        """Create user session."""
        session_token = secrets.token_urlsafe(32)
        session = UserSession(
            session_id=session_token,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
            is_revoked=False,
            version=1,
            expires_at=datetime.now() + timedelta(days=expires_days),
        )
        db.add(session)
        db.commit()
        return session

    def _generate_otp_token(self, db: Session, user_id: int) -> str:
        """Generate OTP token for 2FA."""
        # Generate 6-digit OTP code
        import random

        otp_code = str(random.randint(100000, 999999))

        otp_token = OTPToken(
            user_id=user_id,
            token=otp_code,
            purpose="2fa_verification",
            expires_at=datetime.now() + timedelta(minutes=10),
            is_used=False,
            is_active=True,
            version=1,
        )
        db.add(otp_token)
        db.commit()

        # Send OTP via Email
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            from app.core.email import send_email

            try:
                # Send OTP via email to admin
                admin_email = "avitbulnir@gmail.com"
                email_subject = "OTP Code for Forest Management System"
                email_body = f"""
שלום {user.full_name},

קוד אימות למערכת ניהול יערות: {otp_code}

הקוד תקף ל-10 דקות.

אם לא ביקשת קוד זה, אנא התעלם מהמייל.

בברכה,
מערכת ניהול יערות
"""

                email_result = send_email(
                    to=admin_email, subject=email_subject, body=email_body
                )

                if "successfully" in email_result.get("message", ""):
                    print(
                        f"[AUTH_SERVICE] OTP sent via email to {admin_email} for user: {user.email}"
                    )
                else:
                    print(f"[AUTH_SERVICE] Failed to send OTP via email")

            except Exception as e:
                print(f"[AUTH_SERVICE] Failed to send OTP via email: {e}")

            # Fallback: Print OTP to console
            print(f"[AUTH_SERVICE] OTP CODE FOR {user.email}: {otp_code}")
            print(f"[AUTH_SERVICE] User: {user.full_name}")
            print(f"[AUTH_SERVICE] Expires in 10 minutes")

        return otp_code

    def resend_otp_token(self, db: Session, user_id: int) -> str:
        """Resend OTP token - always generates a new one."""
        print(f"[AUTH_SERVICE] Resending OTP for user {user_id}")

        # סמן את כל ה-OTP הקיימים כמשומשים
        existing_tokens = (
            db.query(OTPToken)
            .filter(
                OTPToken.user_id == user_id,
                OTPToken.purpose == "2fa_verification",
                OTPToken.is_used == False,
                OTPToken.is_active == True,
            )
            .all()
        )

        for token in existing_tokens:
            token.is_used = True
            print(f"[AUTH_SERVICE] Marked old OTP {token.token} as used")

        db.commit()

        # צור OTP חדש
        return self._generate_otp_token(db, user_id)
