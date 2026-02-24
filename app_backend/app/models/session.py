"""
Session model - סשנים של משתמשים
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


class Session(BaseModel):
    """Session model - סשן משתמש - SYNCED WITH DB"""

    __tablename__ = "sessions"

    __table_args__ = {"extend_existing": True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic fields - DB: nvarchar(255), NO / int, NO
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Connection info - DB: nvarchar(45), YES / nvarchar(500), YES
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status - DB: bit, NO / datetime2, NO
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # DB: bit, NO - must have default!
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # DB: int, NO - version field
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, session_id='{self.session_id[:20]}...')>"
