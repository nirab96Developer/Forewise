"""
Location Model - מיקומים
CORE entity - FK to areas
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import Integer, Unicode, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.area import Area


class Location(Base):
    """
    Location model - מיקום
    Table: locations (14 columns)
    Category: CORE
    """
    __tablename__ = "locations"
    __table_args__ = {'implicit_returning': False}  # Has trigger

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic Information
    code: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, unique=True, index=True,
        comment="קוד מיקום"
    )
    
    name: Mapped[str] = mapped_column(
        Unicode(200), nullable=False, index=True,
        comment="שם המיקום"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Unicode, nullable=True,
        comment="תיאור"
    )

    # Foreign Key
    area_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('areas.id'), nullable=False, index=True,
        comment="אזור"
    )

    # Geo coordinates
    latitude: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="קו רוחב"
    )
    
    longitude: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="קו אורך"
    )
    
    address: Mapped[Optional[str]] = mapped_column(
        Unicode(500), nullable=True,
        comment="כתובת"
    )

    # Status
    is_active: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, default=True, server_default='1',
        comment="פעיל"
    )

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, server_default=func.now(),
        comment="תאריך יצירה"
    )
    
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, server_default=func.now(),
        comment="תאריך עדכון"
    )
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="תאריך מחיקה"
    )

    # Version & Metadata
    version: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=1,
        comment="גרסה"
    )
    
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="מטא-דאטא JSON"
    )

    # Relationship
    area: Mapped[Optional["Area"]] = relationship(
        "Area",
        foreign_keys=[area_id],
        lazy="select"
    )

    # Properties
    @property
    def display_name(self) -> str:
        return f"{self.code}: {self.name}" if self.code else self.name
    
    @property
    def coordinates(self) -> Optional[tuple]:
        if self.latitude and self.longitude:
            return (self.latitude, self.longitude)
        return None

    def __repr__(self):
        return f"<Location(id={self.id}, code='{self.code}', name='{self.name}')>"
