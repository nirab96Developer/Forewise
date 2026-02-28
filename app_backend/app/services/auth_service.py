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

    # ─── helpers ─────────────────────────────────────────────

    def _build_user_payload(self, user: User) -> dict:
        role = user.role
        permissions = []
        if role and hasattr(role, "permissions"):
            permissions = [p.code for p in role.permissions]
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": role.code if role else None,
            "permissions": permissions,
            "region_id": user.region_id,
            "area_id": user.area_id,
            "department_id": user.department_id,
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

    # ─── public API ──────────────────────────────────────────

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
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("שם משתמש או סיסמה שגויים")

        remember_me = getattr(login_data, "remember_me", False)

        # 2FA flow
        if getattr(user, "two_factor_enabled", False):
            otp_code = self._generate_otp_token(db, user.id)
            return {
                "requires_2fa": True,
                "user_id": user.id,
                "otp_token": otp_code,
                "user": None,
                "access_token": "",
                "refresh_token": "",
                "token_type": "bearer",
                "expires_in": 0,
            }

        # Direct login
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

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "requires_2fa": False,
            "user": self._build_user_payload(user),
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

    def request_password_reset(self, db: Session, reset_data) -> dict:
        email = getattr(reset_data, "email", "")
        user = db.query(User).filter(User.email == email, User.is_active == True).first()
        # Always return generic message to prevent enumeration
        if user:
            token = self._generate_otp_token(db, user.id)
        return {"message": "אם המייל קיים, תקבל קישור לאיפוס"}

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
        return {"message": "2FA setup not fully implemented", "secret": "", "qr_code": ""}

    def verify_2fa_setup(self, db: Session, user_id: int, code: str) -> bool:
        return True

    def disable_2fa(self, db: Session, user_id: int, code: str = None) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.two_factor_enabled = False
            db.commit()
        return True
