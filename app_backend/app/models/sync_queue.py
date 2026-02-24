"""
SyncQueue model - תור סנכרון אופליין
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


class SyncQueue(BaseModel):
    """SyncQueue model - פריט בתור סנכרון - SYNCED WITH DB"""

    __tablename__ = "sync_queue"

    __table_args__ = {"extend_existing": True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Operation - DB: nvarchar(255), NO
    operation: Mapped[str] = mapped_column(String(255), nullable=False)

    # Entity - DB: nvarchar(100), NO / nvarchar(100), YES
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Data - DB: nvarchar(-1), NO / nvarchar(-1), YES
    data_payload: Mapped[str] = mapped_column(Text, nullable=False)
    original_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # User and device - DB: int, NO / nvarchar(100), YES
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamp - DB: datetime2, NO
    client_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Status - DB: nvarchar(255), NO / nvarchar(255), NO
    status: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(255), nullable=False)

    # Retry - DB: int, NO / int, NO
    attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False)

    # Processing - DB: datetime2, YES
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Error - DB: nvarchar(-1), YES
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Conflict - DB: bit, NO / nvarchar(50), YES / bit, NO
    conflict_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    resolution_strategy: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Relationships
    # user: Mapped["User"] = relationship("User")

    def __repr__(self):
        return f"<SyncQueue(id={self.id}, operation='{self.operation}', status='{self.status}')>"
