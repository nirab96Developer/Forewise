"""
Permission model - הרשאות
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import Integer, Unicode, UnicodeText
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.role import Role


class Permission(BaseModel):
    """Permission model - הרשאה"""
    __tablename__ = "permissions"
    __table_args__ = {'implicit_returning': False}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Unicode(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(UnicodeText, nullable=True)
    resource: Mapped[Optional[str]] = mapped_column(Unicode(50), nullable=True, index=True)
    action: Mapped[Optional[str]] = mapped_column(Unicode(50), nullable=True, index=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Unicode, nullable=True)

    # Relationships
    roles: Mapped[List["Role"]] = relationship("Role", secondary="role_permissions", lazy="select", back_populates="permissions")

    @validates("code")
    def validate_code(self, _key: str, code: str) -> str:
        if not code:
            raise ValueError("Permission code is required")
        code = code.lower().strip()
        if '.' not in code:
            raise ValueError("Permission code should be in format: resource.action")
        return code

    def __repr__(self):
        return f"<Permission(id={self.id}, code='{self.code}')>"
