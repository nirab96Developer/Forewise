"""
ActivityLog model - לוג פעילויות משתמשים
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class ActivityType:
    """Activity type constants"""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    IMPORT = "import"


class ActivityLog(BaseModel):
    """ActivityLog model - לוג פעילות - SYNCED WITH DB"""

    __tablename__ = "activity_logs"

    __table_args__ = {'implicit_returning': False, 'extend_existing': True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # User - DB: int, YES
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Activity - DB: nvarchar(255), NO / nvarchar(200), NO
    activity_type: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(200), nullable=False)

    # Entity - DB: nvarchar(50), YES / int, YES
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Human-readable description (DB column exists)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Category - for role-based filtering: operational, financial, management, system
    category: Mapped[Optional[str]] = mapped_column(String(50), default="system", nullable=True)

    # Connection info - DB: nvarchar(45), YES / nvarchar(500), YES / nvarchar(255), YES
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Details - DB: nvarchar(-1), YES
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status - DB: bit, NOT NULL
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    # user: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, activity_type='{self.activity_type}', action='{self.action}')>"
