"""
SupportTicketComment model - תגובות לפניות תמיכה
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.support_ticket import SupportTicket
    from app.models.user import User


class SupportTicketComment(BaseModel):
    """SupportTicketComment model - תגובה לפנייה - SYNCED WITH DB"""

    __tablename__ = "support_ticket_comments"

    __table_args__ = {"extend_existing": True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys - DB: int, NO / int, NO
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Content - DB: nvarchar(-1), NO
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Visibility - DB: bit, YES, default=0
    is_internal: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)

    # Attachments - DB: nvarchar(-1), YES
    attachments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    # ticket: Mapped["SupportTicket"] = relationship("SupportTicket")
    # user: Mapped["User"] = relationship("User")

    def __repr__(self):
        return f"<SupportTicketComment(id={self.id}, ticket_id={self.ticket_id}, user_id={self.user_id})>"
