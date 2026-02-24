"""
RolePermission - טבלת קשר
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RolePermission(Base):
    """RolePermission - קישור תפקיד-הרשאה"""
    __tablename__ = "role_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('roles.id'), nullable=True)
    permission_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('permissions.id'), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)

    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"
