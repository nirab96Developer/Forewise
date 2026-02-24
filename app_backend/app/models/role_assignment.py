"""
RoleAssignment model - הקצאת תפקידים
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.role import Role


class RoleAssignment(Base):
    """RoleAssignment - הקצאת תפקיד למשתמש"""
    __tablename__ = "role_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey('roles.id'), nullable=False)
    assigned_by: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    scope_type: Mapped[str] = mapped_column(Unicode(50), nullable=False)
    scope_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Unicode, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="joined")
    role: Mapped["Role"] = relationship("Role", foreign_keys=[role_id], lazy="joined")
    assigner: Mapped["User"] = relationship("User", foreign_keys=[assigned_by], lazy="select")

    def __repr__(self):
        return f"<RoleAssignment(user_id={self.user_id}, role_id={self.role_id})>"
