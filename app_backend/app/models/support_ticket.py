"""
SupportTicket model - פניות תמיכה
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import Integer, String, Unicode, Text, UnicodeText, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

if TYPE_CHECKING:
    pass


class SupportTicket(BaseModel):
    """SupportTicket model - פנייה לתמיכה - SYNCED WITH DB"""

    __tablename__ = "support_tickets"

    __table_args__ = {'implicit_returning': False, 'extend_existing': True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic info - DB: nvarchar(50), NO / nvarchar(200), NO / nvarchar(-1), NO
    ticket_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    description: Mapped[str] = mapped_column(UnicodeText, nullable=False)

    # Classification - DB: nvarchar(255), NO
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False)

    # Assignment - DB: int, NO / int, YES
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_to_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Category and tags - DB: nvarchar(100), YES / nvarchar(-1), YES
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Time estimation - DB: int, YES
    estimated_resolution_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_resolution_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Dates - DB: datetimeoffset, YES
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Resolution - DB: nvarchar(-1), YES / nvarchar(-1), YES / int, YES / nvarchar(-1), YES
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    custom_metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # DB: bit, NO
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Relationships
    # user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    # created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])
    # assigned_to: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_id])

    def __repr__(self):
        return f"<SupportTicket(id={self.id}, ticket_number='{self.ticket_number}', status='{self.status}')>"
