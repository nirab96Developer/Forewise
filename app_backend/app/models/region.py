"""
Region model - אזורים
CORE entity
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Unicode, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Region(BaseModel):
    """
    Region model - אזור
    Table: regions (8 columns + audit from migration)
    Category: CORE
    """
    __tablename__ = "regions"
    __table_args__ = {'implicit_returning': False}  # Has triggers

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic Information
    name: Mapped[str] = mapped_column(
        Unicode(200), nullable=False, index=True,
        comment="שם האזור"
    )
    
    code: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True, unique=True, index=True,
        comment="קוד אזור"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="תיאור"
    )

    # Foreign Key
    manager_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=True, index=True,
        comment="מנהל אזור"
    )
    
    # Budget
    total_budget: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, default=0,
        comment="תקציב כולל למרחב"
    )

    # Audit from BaseModel: created_at, updated_at, deleted_at, is_active, version

    # Relationship
    manager: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[manager_id],
        lazy="select"
    )

    # Properties
    @property
    def display_name(self) -> str:
        return f"{self.code}: {self.name}" if self.code else self.name

    def __repr__(self):
        return f"<Region(id={self.id}, name='{self.name}')>"
