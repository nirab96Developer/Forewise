"""AuthService — business logic for authentication."""

import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.otp_token import OTPToken
from app.models.session import Session as UserSession
from app.models.user import User
from app.models.role import Role


class AuthService:

# helpers 

    def _build_user_payload(self, user: User) -> dict:
        role = user.role
        permissions = []
        if role and hasattr(role, "permissions"):
            permissions = [p.code for p in role.permissions]
        full_name = user.full_name or ""
        first_name = full_name.split()[0] if full_name.strip() else full_name
        last_login_iso = user.last_login.isoformat() if getattr(user, "last_login", None) else None
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": full_name,
            "first_name": first_name,
            "role": role.code if role else None,
            "role_code": role.code if role else None,
            "permissions": permissions,
            "region_id": user.region_id,
            "area_id": user.area_id,
            "department_id": user.department_id,
            "must_change_password": bool(getattr(user, "must_change_password", False)),
            "last_login": last_login_iso,
        }

    def _load_user(self, db: Session, user_id: int) -> Optional[User]:
        return (
            db.query(User)
            .options(selectinload(User.role).selectinload(Role.permissions))
            .filter(User.id == user_id, User.is_active == True)
            .first()
        )

    def _generate_otp_token(self, db: Session, user_id: int) -> str:
        """Create and persist a 6-digit OTP; returns the plain code."""
        # Invalidate previous
        db.query(OTPToken).filter(
            OTPToken.user_id == user_id,
            OTPToken.is_used == False,
            OTPToken.is_active == True,
        ).update({"is_active": False})

        code = "".join(secrets.choice(string.digits) for _ in range(6))
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        otp = OTPToken(
            user_id=user_id,
            token=code,
            token_hash=code_hash,
            code_hash=code_hash,
            purpose="login",
            expires_at=datetime.now() + timedelta(minutes=10),
            is_used=False,
            is_active=True,
            attempts=0,
        )
        db.add(otp)
        db.commit()
        return code

# public API 

    def lock_account(self, db: Session, user_id: int, reason: str = None, duration_hours: int = None) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("משתמש לא נמצא")
        user.is_locked = True
        if duration_hours:
            user.locked_until = datetime.now() + timedelta(hours=duration_hours)
        db.commit()
        return True

    def unlock_account(self, db: Session, user_id: int, reason: str = None) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("משתמש לא נמצא")
        user.is_locked = False
        user.locked_until = None
        db.commit()
        return True

    def login(self, db: Session, login_data, ip_address=None, user_agent=None) -> dict:
        username = login_data.username.strip()
        password = login_data.password

        user = (
            db.query(User)
            .options(selectinload(User.role).selectinload(Role.permissions))
            .filter(
                (User.username == username) | (User.email == username),
                User.is_active == True,
            )
            .first()
        )

        if user and getattr(user, "is_locked", False):
            locked_until = getattr(user, "locked_until", None)
            if locked_until and locked_until > datetime.now():
                raise ValueError("החשבון נעול זמנית. נסה שוב מאוחר יותר")
            elif locked_until and locked_until <= datetime.now():
                user.is_locked = False
                user.locked_until = None
                db.commit()

        if not user or not verify_password(password, user.password_hash):
            if user:
                from app.core.rate_limiting import lock_account_on_failure
                failed = getattr(user, "failed_login_attempts", 0) or 0
                user.failed_login_attempts = failed + 1
                if user.failed_login_attempts >= 5:
                    user.is_locked = True
                    user.locked_until = datetime.now() + timedelta(minutes=15)
                db.commit()
                lock_account_on_failure(username, user.failed_login_attempts)
            raise ValueError("שם משתמש או סיסמה שגויים")

        remember_me = getattr(login_data, "remember_me", False)

        # 2FA flow — also require OTP on first login (must_change_password)
        is_first_login = bool(getattr(user, "must_change_password", False)) and not getattr(user, "last_login", None)
        if getattr(user, "two_factor_enabled", False) or is_first_login:
            otp_code = self._generate_otp_token(db, user.id)

            # Send OTP via email (best-effort)
            try:
                from app.core.email import send_email
                full_name = user.full_name or user.username or "משתמש"
                subject = "קוד אימות — כניסה למערכת Forewise"
                body = (
                    f"שלום {full_name},\n\n"
                    f"קוד האימות שלך הוא:\n\n"
                    f"    {otp_code}\n\n"
                    f"הקוד תקף ל-10 דקות.\n\n"
                    "אם לא ביקשת להתחבר, התעלם מהודעה זו.\n\n"
                    "Forewise"
                )
                html_body = f"""
<div dir="rtl" style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;">
  <div style="background:#2d6a2d;color:#fff;padding:20px 24px;border-radius:8px 8px 0 0;">
<h2 style="margin:0;">קוד אימות — Forewise </h2>
  </div>
  <div style="padding:28px 24px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 8px 8px;">
    <p>שלום <strong>{full_name}</strong>,</p>
    <p>קוד האימות שלך לכניסה למערכת:</p>
    <div style="text-align:center;margin:24px 0;">
      <span style="font-size:40px;font-weight:bold;letter-spacing:12px;color:#1a1a1a;font-family:monospace;">{otp_code}</span>
    </div>
    <p style="color:#6b7280;font-size:13px;">הקוד תקף ל-10 דקות בלבד.</p>
    <p style="color:#6b7280;font-size:13px;">אם לא ביקשת להתחבר — התעלם מהודעה זו.</p>
    <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;"/>
    <p style="color:#9ca3af;font-size:12px;">Forewise — מערכת ניהול הזמנות</p>
  </div>
</div>"""
                send_email(to=user.email, subject=subject, body=body, html_body=html_body)
                import logging
                logging.getLogger(__name__).info(f"OTP email sent to {user.email}")
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to send OTP email to {user.email}: {e}")

            return {
                "requires_2fa": True,
                "is_first_login": is_first_login,
                "user_id": user.id,
                "user": None,
                "access_token": "",
                "refresh_token": "",
                "token_type": "bearer",
                "expires_in": 0,
            }

        # Reset failed attempts on successful login
        if getattr(user, "failed_login_attempts", 0):
            user.failed_login_attempts = 0

        # Direct login — save previous login time before updating
        previous_login = user.last_login
        user.last_login = datetime.now()
        access_token = create_access_token(
            {"sub": str(user.id), "email": user.email, "role": user.role.code if user.role else ""}
        )
        expire_days = 30 if remember_me else 7
        refresh_token = create_refresh_token({"sub": str(user.id)}, expires_delta=timedelta(days=expire_days))

        session = UserSession(
            session_id=secrets.token_urlsafe(32),
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now() + timedelta(days=expire_days),
        )
        db.add(session)
        db.commit()

        payload = self._build_user_payload(user)
        # Override last_login with PREVIOUS session (not current login time)
        payload["last_login"] = previous_login.isoformat() if previous_login else None

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "requires_2fa": False,
            "user": payload,
        }

    def verify_2fa(self, db: Session, user_id: int, code: str, backup_code=None) -> dict:
        code_clean = str(code).strip()
        otp = (
            db.query(OTPToken)
            .filter(
                OTPToken.user_id == user_id,
                OTPToken.token == code_clean,
                OTPToken.is_used == False,
                OTPToken.is_active == True,
                OTPToken.expires_at > datetime.now(),
            )
            .first()
        )
        if not otp:
            raise ValueError("קוד שגוי או פג תוקף")

        otp.is_used = True
        otp.is_active = False
        otp.used_at = datetime.now()

        user = self._load_user(db, user_id)
        if not user:
            raise ValueError("משתמש לא נמצא")

        user.last_login = datetime.now()
        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "requires_2fa": False,
            "user": self._build_user_payload(user),
        }

    def refresh_token(self, db: Session, refresh_token: str) -> dict:
        from app.core.security import decode_token
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise ValueError("Refresh token invalid or expired")
        if not payload:
            raise ValueError("Refresh token invalid or expired")
        user_id = int(payload.get("sub", 0))
        user = self._load_user(db, user_id)
        if not user:
            raise ValueError("User not found")
        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        return {"access_token": access_token, "token_type": "bearer", "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60}

    def logout(self, db: Session, access_token: str, refresh_token: str = None, all_sessions: bool = False):
        pass  # token blacklisting handled by api interceptor

    def change_password(self, db: Session, user_id: int, current_password: str, new_password: str) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not verify_password(current_password, user.password_hash):
            return False
        user.password_hash = get_password_hash(new_password)
        db.commit()
        return True

    def _generate_reset_token(self, db: Session, user_id: int) -> str:
        """Create a password-reset OTP with correct purpose."""
        db.query(OTPToken).filter(
            OTPToken.user_id == user_id,
            OTPToken.purpose == "password_reset",
            OTPToken.is_used == False,
            OTPToken.is_active == True,
        ).update({"is_active": False})

        code = "".join(secrets.choice(string.digits) for _ in range(6))
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        otp = OTPToken(
            user_id=user_id,
            token=code,
            token_hash=code_hash,
            code_hash=code_hash,
            purpose="password_reset",
            expires_at=datetime.now() + timedelta(minutes=15),
            is_used=False,
            is_active=True,
            attempts=0,
        )
        db.add(otp)
        db.commit()
        return code

    def request_password_reset(self, db: Session, reset_data) -> dict:
        email = getattr(reset_data, "email", "")
        user = db.query(User).filter(User.email == email, User.is_active == True).first()
        if user:
            token = self._generate_reset_token(db, user.id)
            try:
                from app.core.email import send_email
                full_name = user.full_name or user.email
                html_body = f"""
<div dir="rtl" style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;">
  <div style="background:#2d6a2d;color:#fff;padding:20px 24px;border-radius:8px 8px 0 0;">
<h2 style="margin:0;">איפוס סיסמה — Forewise </h2>
  </div>
  <div style="padding:28px 24px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 8px 8px;">
    <p>שלום <strong>{full_name}</strong>,</p>
    <p>קוד האימות לאיפוס הסיסמה שלך:</p>
    <div style="text-align:center;margin:24px 0;">
      <span style="font-size:40px;font-weight:bold;letter-spacing:12px;color:#1a1a1a;font-family:monospace;">{token}</span>
    </div>
    <p style="color:#6b7280;font-size:13px;">הקוד תקף ל-15 דקות בלבד.</p>
    <p style="color:#6b7280;font-size:13px;">אם לא ביקשת לאפס סיסמה — התעלם מהודעה זו.</p>
    <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;"/>
    <p style="color:#9ca3af;font-size:12px;">Forewise — מערכת ניהול הזמנות</p>
  </div>
</div>"""
                send_email(
                    to=user.email,
                    subject="איפוס סיסמה — Forewise",
                    body=f"שלום {full_name},\n\nקוד האימות לאיפוס הסיסמה שלך: {token}\n\nהקוד תקף ל-15 דקות.\n\nForewise",
                    html_body=html_body,
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to send reset email to {user.email}: {e}")
        return {"message": "אם המייל קיים במערכת, נשלח אליך קוד לאיפוס סיסמה"}

    def reset_password(self, db: Session, token: str, new_password: str) -> bool:
        otp = db.query(OTPToken).filter(
            OTPToken.token == token,
            OTPToken.purpose == "password_reset",
            OTPToken.is_used == False,
            OTPToken.is_active == True,
            OTPToken.expires_at > datetime.now(),
        ).first()
        if not otp:
            return False
        user = db.query(User).filter(User.id == otp.user_id).first()
        if not user:
            return False
        user.password_hash = get_password_hash(new_password)
        otp.is_used = True
        otp.is_active = False
        db.commit()
        return True

    def setup_2fa(self, db: Session, user_id: int) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("משתמש לא נמצא")
        user.two_factor_enabled = True
        db.commit()
        return {"enabled": True}

    def verify_2fa_setup(self, db: Session, user_id: int, code: str) -> bool:
        if not code or len(code) < 4:
            raise ValueError("קוד לא תקין")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("משתמש לא נמצא")
        return user.two_factor_enabled is True

    def disable_2fa(self, db: Session, user_id: int, code: str = None) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("משתמש לא נמצא")
        user.two_factor_enabled = False
        db.commit()
        return True
