"""
AuditLog model - לוג ביקורת
SYNCED WITH DB - 17.11.2025
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(BaseModel):
    """AuditLog model - רשומת ביקורת - SYNCED WITH DB"""

    __tablename__ = "audit_logs"

    __table_args__ = {"extend_existing": True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # User - DB: int, YES
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Action - DB: nvarchar(100), NO
    action: Mapped[str] = mapped_column(String(100), nullable=False)

    # Entity - DB: nvarchar(50), YES / int, YES
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Connection - DB: nvarchar(45), YES / nvarchar(255), YES
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Data - DB: nvarchar(-1), YES
    old_values: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_values: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audit_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Severity - DB: nvarchar(20), NO / nvarchar(20), YES
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Error - DB: nvarchar(500), YES
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # DB: bit, NO
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Relationships
    # user: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', severity='{self.severity}')>"
