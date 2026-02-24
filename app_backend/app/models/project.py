"""
Project Model - פרויקטים
CORE entity - The heart of the system
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import Integer, Unicode, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.region import Region
    from app.models.area import Area
    from app.models.location import Location
    from app.models.budget import Budget


class Project(Base):
    """
    Project model - פרויקט
    Table: projects (12 columns + deleted_at, version from migration)
    Category: CORE
    """
    __tablename__ = "projects"
    __table_args__ = {'implicit_returning': False}  # Has trigger

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic Information
    name: Mapped[str] = mapped_column(
        Unicode(200), nullable=False, index=True,
        comment="שם הפרויקט"
    )
    
    code: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, unique=True, index=True,
        comment="קוד פרויקט"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="תיאור"
    )

    # Foreign Keys - Required
    manager_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), nullable=False, index=True,
        comment="מנהל פרויקט"
    )
    
    region_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('regions.id'), nullable=False, index=True,
        comment="אזור"
    )
    
    area_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('areas.id'), nullable=False, index=True,
        comment="אזור משני"
    )
    
    location_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('locations.id'), nullable=False, index=True,
        comment="מיקום"
    )
    
    # Optional FK
    budget_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('budgets.id'), nullable=True, index=True,
        comment="תקציב"
    )

    # Status
    status: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True, default="active",
        comment="סטטוס פרויקט"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default='1',
        comment="פעיל"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(),
        comment="תאריך יצירה"
    )
    
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, server_default=func.now(),
        comment="תאריך עדכון"
    )
    
    # Added by migration
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="תאריך מחיקה"
    )
    
    version: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=1,
        comment="גרסה"
    )

    # Relationships
    manager: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[manager_id],
        lazy="select"
    )
    
    region: Mapped[Optional["Region"]] = relationship(
        "Region",
        foreign_keys=[region_id],
        lazy="select"
    )
    
    area: Mapped[Optional["Area"]] = relationship(
        "Area",
        foreign_keys=[area_id],
        lazy="select"
    )
    
    location: Mapped[Optional["Location"]] = relationship(
        "Location",
        foreign_keys=[location_id],
        lazy="select"
    )
    
    budget: Mapped[Optional["Budget"]] = relationship(
        "Budget",
        foreign_keys=[budget_id],
        lazy="select"
    )

    # Properties
    @property
    def display_name(self) -> str:
        return f"{self.code}: {self.name}" if self.code else self.name

    def __repr__(self):
        return f"<Project(id={self.id}, code='{self.code}', name='{self.name}')>"
