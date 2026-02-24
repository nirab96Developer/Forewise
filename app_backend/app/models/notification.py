"""
Notification model - התראות
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import Integer, String, Unicode, Text, UnicodeText, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Notification(BaseModel):
    """Notification model - התראה - SYNCED WITH DB"""

    __tablename__ = "notifications"

    __table_args__ = {"extend_existing": True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # User - DB: int, YES
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Basic info - DB: nvarchar(50), YES / nvarchar(255), YES / nvarchar(-1), YES
    type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notification_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(Unicode(255), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(UnicodeText, nullable=True)
    data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Priority and channel - DB: nvarchar(20), YES / nvarchar(50), YES
    priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Read status - DB: bit, YES, default=0 / datetime2, YES
    is_read: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Send status - DB: bit, YES, default=0 / datetime, YES / nvarchar(50), YES
    is_sent: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivery_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Entity - DB: nvarchar(100), YES / int, YES
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Action - DB: nvarchar(500), YES / datetime, YES
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    # user: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, title='{self.title}')>"
