"""
OTPToken model - טוקנים חד-פעמיים (2FA)
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class OTPToken(BaseModel):
    """OTPToken model - טוקן חד-פעמי - SYNCED WITH DB"""

    __tablename__ = "otp_tokens"

    __table_args__ = {"extend_existing": True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic fields - DB: int, NO / nvarchar(255), NO / nvarchar(100), NO
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    token_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    purpose: Mapped[str] = mapped_column(String(100), nullable=False)

    # Expiry - DB: datetime2, NO
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Status - DB: bit, NO
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # DB: int, NO
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")

    def __repr__(self):
        return f"<OTPToken(id={self.id}, user_id={self.user_id}, purpose='{self.purpose}')>"
