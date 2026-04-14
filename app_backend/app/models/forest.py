"""
Forest Model - יערות
מודל לאחסון גבולות יערות ומידע גיאוגרפי
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, Unicode, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.models.base import Base


class Forest(Base):
    """
    Forest model - יער
    Table: forests
    Contains forest boundaries as MultiPolygon geometry
    """
    __tablename__ = "forests"
    __table_args__ = {'extend_existing': True}

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic Information
    name: Mapped[str] = mapped_column(
        Unicode(200), nullable=False, index=True,
        comment="שם היער"
    )
    
    code: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True, unique=True, index=True,
        comment="קוד יער"
    )
    
    # Geometry - PostGIS MultiPolygon
    geom: Mapped[Optional[str]] = mapped_column(
        Geometry(geometry_type='MULTIPOLYGON', srid=4326),
        nullable=False,
        comment="גבולות היער"
    )
    
    # Area in km²
    area_km2: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True,
        comment="שטח בקמ״ר"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(),
        comment="תאריך יצירה"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now(),
        comment="תאריך עדכון"
    )

    def __repr__(self):
        return f"<Forest(id={self.id}, name='{self.name}', code='{self.code}')>"

