"""
Supplier model - ספקים
CORE entity with full audit columns
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Supplier(BaseModel):
    """
    Supplier model - ספק
    Table: suppliers
    Category: CORE (has created_at, updated_at, deleted_at, is_active, version)
    
    Represents a supplier in the system.
    No foreign keys - standalone entity.
    """
    __tablename__ = "suppliers"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic Information - name is NOT NULL + UNIQUE!
    name: Mapped[str] = mapped_column(
        Unicode(200), nullable=False, unique=True, index=True,
        comment="שם הספק (ייחודי, חובה)"
    )
    
    code: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True, unique=True, index=True,
        comment="קוד ספק ייחודי"
    )
    
    tax_id: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True, unique=True, index=True,
        comment="מספר עוסק מורשה / ח.פ"
    )

    # Contact Information
    contact_name: Mapped[Optional[str]] = mapped_column(
        Unicode(100), nullable=True,
        comment="שם איש קשר"
    )
    
    phone: Mapped[Optional[str]] = mapped_column(
        Unicode(20), nullable=True, index=True,
        comment="טלפון"
    )
    
    email: Mapped[Optional[str]] = mapped_column(
        Unicode(255), nullable=True, index=True,
        comment="אימייל"
    )
    
    address: Mapped[Optional[str]] = mapped_column(
        Unicode(500), nullable=True,
        comment="כתובת"
    )

    # Classification
    supplier_type: Mapped[Optional[str]] = mapped_column(
        Unicode(50), nullable=True, index=True,
        comment="סוג ספק: equipment, labor, materials, services"
    )
    
    region_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("regions.id"), nullable=True, index=True,
        comment="מזהה מרחב/אזור ראשי"
    )
    
    area_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("areas.id"), nullable=True, index=True,
        comment="מזהה אזור"
    )

    # Performance Metrics
    rating: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 2), nullable=True,
        comment="דירוג (0.00-5.00)"
    )
    
    priority_score: Mapped[int] = mapped_column(
        Integer, nullable=True, default=0,
        comment="ציון עדיפות (rotation)"
    )
    
    average_response_time: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="זמן תגובה ממוצע (דקות)"
    )
    
    last_selected: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="מתי נבחר לאחרונה"
    )

    # Audit columns inherited from BaseModel:
    # created_at, updated_at, deleted_at, is_active, version

    # No relationships - avoid circular imports
    # work_orders, rotations, constraints - handled elsewhere

    # Properties
    @property
    def display_name(self) -> str:
        """Display name for UI"""
        return f"{self.code}: {self.name}" if self.code else self.name

    @property
    def has_contact(self) -> bool:
        """Check if supplier has contact information"""
        return bool(self.phone or self.email)

    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', code='{self.code}')>"
