"""
User model - משתמשי המערכת
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.department import Department
    from app.models.region import Region
    from app.models.area import Area
    from app.models.session import Session
    from app.models.otp_token import OTPToken
    from app.models.device_token import DeviceToken
    from app.models.biometric_credential import BiometricCredential


class User(BaseModel):
    """User model - משתמש מערכת"""
    __tablename__ = "users"
    __table_args__ = {'implicit_returning': False}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic fields
    username: Mapped[Optional[str]] = mapped_column(Unicode(50), nullable=True, unique=True, index=True)
    email: Mapped[str] = mapped_column(Unicode(255), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(Unicode(20), nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(Unicode(255), nullable=False)

    # Auth fields
    two_factor_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    must_change_password: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    is_locked: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failed_login_attempts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Lifecycle / suspension fields
    suspended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    suspension_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scheduled_deletion_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    previous_role_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('roles.id', ondelete='SET NULL'), nullable=True)

    # Organization
    role_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('roles.id'), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('departments.id'), nullable=True)
    region_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('regions.id'), nullable=True)
    area_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('areas.id'), nullable=True)
    manager_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)

    # Additional
    scope_level: Mapped[Optional[str]] = mapped_column(Unicode(50), nullable=True)
    status: Mapped[str] = mapped_column(Unicode(20), nullable=False, default='ACTIVE')
    metadata_json: Mapped[Optional[str]] = mapped_column(Unicode, nullable=True)

    # Relationships
    role: Mapped[Optional["Role"]] = relationship("Role", foreign_keys=[role_id], lazy="joined", back_populates="users")
    department: Mapped[Optional["Department"]] = relationship("Department", foreign_keys=[department_id], lazy="select")
    region: Mapped[Optional["Region"]] = relationship("Region", foreign_keys=[region_id], lazy="select")
    area: Mapped[Optional["Area"]] = relationship("Area", foreign_keys=[area_id], lazy="select")
    manager: Mapped[Optional["User"]] = relationship("User", remote_side=[id], foreign_keys=[manager_id], lazy="select", back_populates="subordinates")
    subordinates: Mapped[List["User"]] = relationship("User", foreign_keys=[manager_id], lazy="select", back_populates="manager")
    sessions: Mapped[List["Session"]] = relationship("Session", cascade="all, delete-orphan", lazy="select", back_populates="user")
    otp_tokens: Mapped[List["OTPToken"]] = relationship("OTPToken", cascade="all, delete-orphan", lazy="select")
    device_tokens: Mapped[List["DeviceToken"]] = relationship("DeviceToken", cascade="all, delete-orphan", lazy="select")
    biometric_credentials: Mapped[List["BiometricCredential"]] = relationship("BiometricCredential", cascade="all, delete-orphan", lazy="select", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
