"""
Area Model - אזורים משניים
CORE entity - FK to regions
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Unicode, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.region import Region


class Area(BaseModel):
    """
    Area model - אזור משני
    Table: areas (11 columns + audit from migration)
    Category: CORE
    """
    __tablename__ = "areas"
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

    # Foreign Keys
    region_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('regions.id'), nullable=True, index=True,
        comment="אזור ראשי"
    )
    
    manager_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=True, index=True,
        comment="מנהל אזור"
    )
    
    # Business fields
    total_area_hectares: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="שטח כולל בהקטרים"
    )

    # Audit from BaseModel: created_at, updated_at, deleted_at, is_active, version

    # Relationships
    region: Mapped[Optional["Region"]] = relationship(
        "Region",
        foreign_keys=[region_id],
        lazy="select"
    )
    
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
        return f"<Area(id={self.id}, name='{self.name}')>"
