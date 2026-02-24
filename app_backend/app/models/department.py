"""
Department Model - מחלקות
CORE entity - Self-referential hierarchy
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Unicode, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Department(BaseModel):
    """
    Department model - מחלקה
    Table: departments (12 columns)
    Category: CORE
    """
    __tablename__ = "departments"
    __table_args__ = {'implicit_returning': False}  # Has trigger

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic Information - Both required
    code: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, unique=True, index=True,
        comment="קוד מחלקה"
    )
    
    name: Mapped[str] = mapped_column(
        Unicode(200), nullable=False, index=True,
        comment="שם המחלקה"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="תיאור"
    )

    # Foreign Keys
    manager_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=True, index=True,
        comment="מנהל מחלקה"
    )
    
    # Self-referential - parent department
    parent_department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('departments.id'), nullable=True, index=True,
        comment="מחלקת אב"
    )
    
    # Extra data
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="מטא-דאטא JSON"
    )

    # Audit from BaseModel: created_at, updated_at, deleted_at, is_active, version

    # Relationships
    manager: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[manager_id],
        lazy="select"
    )
    
    parent: Mapped[Optional["Department"]] = relationship(
        "Department",
        foreign_keys=[parent_department_id],
        remote_side=[id],
        lazy="select"
    )

    # Properties
    @property
    def display_name(self) -> str:
        return f"{self.code}: {self.name}" if self.code else self.name

    def __repr__(self):
        return f"<Department(id={self.id}, code='{self.code}', name='{self.name}')>"
