"""
Role model - תפקידים
"""
from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import Integer, String, Unicode, UnicodeText
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.permission import Permission


class RoleCode(str, enum.Enum):
    ADMIN = "ADMIN"
    REGION_MANAGER = "REGION_MANAGER"
    AREA_MANAGER = "AREA_MANAGER"
    WORK_MANAGER = "WORK_MANAGER"
    ACCOUNTANT = "ACCOUNTANT"
    SUPPLIER = "SUPPLIER"
    VIEWER = "VIEWER"


class Role(BaseModel):
    """Role model - תפקיד"""
    __tablename__ = "roles"
    __table_args__ = {'implicit_returning': False}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Unicode(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(UnicodeText, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=99)
    metadata_json: Mapped[Optional[str]] = mapped_column(Unicode, nullable=True)

    # Relationships
    users: Mapped[List["User"]] = relationship("User", foreign_keys="User.role_id", lazy="select")
    permissions: Mapped[List["Permission"]] = relationship("Permission", secondary="role_permissions", lazy="select")

    @validates("code")
    def validate_code(self, _key: str, code: str) -> str:
        if not code:
            raise ValueError("Role code is required")
        code = code.upper().strip()
        if not code.replace("_", "").isalnum():
            raise ValueError("Code can only contain letters, numbers and underscore")
        return code

    def __repr__(self):
        return f"<Role(id={self.id}, code='{self.code}')>"
