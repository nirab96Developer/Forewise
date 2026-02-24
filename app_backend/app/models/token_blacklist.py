"""
TokenBlacklist model - רשימת טוקנים חסומים
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class TokenBlacklist(BaseModel):
    """TokenBlacklist model - טוקן חסום - SYNCED WITH DB"""

    __tablename__ = "token_blacklist"

    __table_args__ = {"extend_existing": True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Token details - DB: varchar(255), NO / varchar(-1), NO
    jti: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    token: Mapped[str] = mapped_column(String(5000), nullable=False)  # varchar(-1) = very long

    # User - DB: int, YES
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    blacklisted_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Reason - DB: varchar(255), YES
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # IP - DB: varchar(45), YES
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Dates - DB: datetime, NO / datetime, YES
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default="getdate()", nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    # user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    # blacklisted_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[blacklisted_by_id])

    def __repr__(self):
        return f"<TokenBlacklist(id={self.id}, jti='{self.jti[:20]}...', user_id={self.user_id})>"
